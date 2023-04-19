'''
Tate Thomas
CS 3060 - Project 4: CPU Scheduler Simulator
'''

import sys


class Process:
    '''Class to hold data for a process'''

    def __init__(self, create_time, run_time, p_id):
        # initial data attributes
        self._create_time = create_time  # arrival time to CPU
        self._run_time = run_time    # burst time for process
        self._p_id = p_id    # identifier

        # runtime attributes
        self.time_remaining = run_time
        self.burst_start = None
        self.time_paused = create_time     # time at which the process is preempted

        # final statistics
        self._wait_time = 0
        self._response_time = None
        self._turnaround_time = None

    def get_response_time(self):
        '''Getter for process response time'''

        return self._response_time

    def get_wait_time(self):
        '''Getter for process wait time'''

        return self._wait_time

    def get_turnaround_time(self):
        '''Getter for process turaround time'''

        return self._turnaround_time


class Scheduler:
    '''Abstract class for a CPU scheduler'''

    def __init__(self, p_list):
        # bookkeeping for scheduler
        self._p_list = p_list.copy()   # list of processes, which is a tuple of the arrival time and burst time
        self._p_list.sort(key=lambda x: x[0])    # sort by arrival time
        self._queue = []    # list of Process objects waiting to be run
        self._running = None    # Process object currently being ran
        self._done = []     # list of Process objects whose task has finished

        # runtime attributes
        self._clock = 0
        self._p_id_counter = 0

        # final statistics
        self._avg_response = 0
        self._avg_wait = 0
        self._avg_turnaround = 0

    def create_process(self, p_data):
        '''Creates a new Process object'''

        new_p = Process(p_data[0], p_data[1], self._p_id_counter)
        self._p_id_counter += 1
        return new_p

    def start_process(self, p):
        '''Starts a given process in the CPU scheduler'''

        p.burst_start = self._clock     # update start time of new burst
        if p._response_time is None:
            p._response_time = self._clock - p._create_time
        p._wait_time += p.burst_start - p.time_paused   # add to the total wait time
        self._running = p

    def stop_process(self):
        '''Stops whatever process is currently running'''

        if self._running is None:
            return
        p = self._running
        p.time_paused = self._clock     # update the time the process was stopped at
        self._running = None
        if p.time_remaining > 0:
            self._queue.append(p)
        else:
            self._done.append(p)
            p._turnaround_time = self._clock + 1 - p._create_time

    def progress_p(self):
        '''Make progress on currently running process'''

        if self._running is None:
            return
        p = self._running
        p.time_remaining -= 1
        if p.time_remaining == 0:
            self.stop_process()

    def calc_averages(self):
        '''Calculate the average response time, wait time, and turnaround time for completed processes'''

        for p in self._done:
            self._avg_response += p.get_response_time()
            self._avg_wait += p.get_wait_time()
            self._avg_turnaround += p.get_turnaround_time()
        self._avg_response /= len(self._done)
        self._avg_wait /= len(self._done)
        self._avg_turnaround /= len(self._done)

    def get_statistics(self):
        '''Get current statistics of the CPU scheduler'''

        return (self._avg_response, self._avg_wait, self._avg_turnaround)


class FCFS(Scheduler):
    '''Class implementing the First Come, First Serve scheduling algorithm'''

    def run(self):
        '''Execute processes from the initial process list given'''

        p_index = 0     # index for traversing initial list of processes given
        while True:

            # check for new processes arriving
            while (p_index < len(self._p_list)) and (self._p_list[p_index][0] == self._clock):
                new_p = self.create_process(self._p_list[p_index])
                self._queue.append(new_p)
                p_index += 1

            # start running a process if none are currently being ran
            if self._running is None:
                if len(self._queue) > 0:
                    super().start_process(self._queue.pop(0))
                elif p_index == len(self._p_list):
                    break   # no more processes left

            super().progress_p()
            self._clock += 1

        self.calc_averages()


class SJF(Scheduler):
    '''Class implementing the Shortest Job First scheduling algorithm'''

    def run(self):
        '''Execute processes from the initial process list given'''

        p_index = 0
        while True:

            # check for new processes arriving
            while (p_index < len(self._p_list)) and (self._p_list[p_index][0] == self._clock):
                new_p = self.create_process(self._p_list[p_index])
                self._queue.append(new_p)
                self._queue.sort(key=lambda x: x._run_time)
                p_index += 1

            # start running a process if none are currently being ran
            if self._running is None:
                if len(self._queue) > 0:
                    super().start_process(self._queue.pop(0))
                elif p_index == len(self._p_list):
                    break   # no more processes left

            super().progress_p()
            self._clock += 1

        self.calc_averages()


class SRTF(Scheduler):
    '''Class implementing the Shortest Run-Time First scheduling algorithm'''

    def run(self):
        '''Execute processes from the initial process list given'''

        p_index = 0

        while True:

            # check for new processes arriving
            while (p_index < len(self._p_list)) and (self._p_list[p_index][0] == self._clock):
                new_p = self.create_process(self._p_list[p_index])
                self._queue.append(new_p)
                self._queue.sort(key=lambda x: x.time_remaining)
                p_index += 1

            # start running a process if none are currently being ran
            if self._running is None:
                if len(self._queue) > 0:
                    super().start_process(self._queue.pop(0))
                elif p_index == len(self._p_list):
                    break   # no more processes left

            elif (len(self._queue) > 0) and (self._queue[0].time_remaining < self._running.time_remaining):
                # new process has shorter time remaining than whats currently running
                super().stop_process()
                self._queue.sort(key=lambda x: x.time_remaining)
                super().start_process(self._queue.pop(0))

            super().progress_p()
            self._clock += 1

        self.calc_averages()


class RR(Scheduler):
    '''Class implementing the Round Robin scheduling algorithm'''

    def __init__(self, p_list, t_quantum):
        super().__init__(p_list)
        self.t_quantum = t_quantum
        self._q_clock = t_quantum   # clock to track the current processes burst time, switch when it hits 0

    def start_process(self, p):
        '''Starts a given process in the RR CPU scheduler'''

        super().start_process(p)
        self._q_clock = self.t_quantum  # resent the time quantum counter

    def run(self):
        '''Execute processes from the initial process list given'''

        p_index = 0
        while True:

            # check for new processes arriving
            while (p_index < len(self._p_list)) and (self._p_list[p_index][0] == self._clock):
                new_p = self.create_process(self._p_list[p_index])
                self._queue.append(new_p)
                p_index += 1

            # start running a process if none are currently being ran
            if self._running is None:
                if len(self._queue) > 0:
                    self.start_process(self._queue.pop(0))
                elif p_index == len(self._p_list):
                    break   # no more processes left

            elif self._q_clock == 0:
                # max duration of time quantum reached, switch processes if new ones are availible
                if len(self._queue) > 0:
                    super().stop_process()
                    self.start_process(self._queue.pop(0))
                else:
                    self._q_clock = self.t_quantum  # no new processes, continue current process

            super().progress_p()
            self._clock += 1
            self._q_clock -= 1

        self.calc_averages()


def main():
    '''Take input from command line (Time quantum, < Process list txt), run on each CPU scheduling algorithm, print results'''

    time_quantum = 100 	# default
    if len(sys.argv) > 1:
        time_quantum = int(sys.argv[1])

    # format input to list of tuples
    p_list = []
    for line in sys.stdin.readlines():
        p_data = line.strip().split()
        p_list.append((int(p_data[0]), int(p_data[1])))     # process data tuple (arrival time, burst time)

    # simulate with each scheduling algorithm
    fcfs = FCFS(p_list)
    fcfs.run()
    fcfs_stat = fcfs.get_statistics()

    sjf = SJF(p_list)
    sjf.run()
    sjf_stat = sjf.get_statistics()

    srtf = SRTF(p_list)
    srtf.run()
    srtf_stat = srtf.get_statistics()

    rr = RR(p_list, time_quantum)
    rr.run()
    rr_stat = rr.get_statistics()

    # output results
    print(f"First Come, First Served\nAvg. Resp.:{fcfs_stat[0]:.2f}, Avg. T.A.:{fcfs_stat[2]:.2f}, Avg. Wait:{fcfs_stat[1]:.2f}\n")
    print(f"Shortest Job First\nAvg. Resp.:{sjf_stat[0]:.2f}, Avg. T.A.:{sjf_stat[2]:.2f}, Avg. Wait:{sjf_stat[1]:.2f}\n")
    print(f"Shortest Remaining Time First\nAvg. Resp.:{srtf_stat[0]:.2f}, Avg. T.A.:{srtf_stat[2]:.2f}, Avg. Wait:{srtf_stat[1]:.2f}\n")
    print(f"Round Robin with Time Quantum of {rr.t_quantum}\nAvg. Resp.:{rr_stat[0]:.2f}, Avg. T.A.:{rr_stat[2]:.2f}, Avg. Wait:{rr_stat[1]:.2f}")


if __name__ == "__main__":
    main()
