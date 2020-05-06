
import time
def save(data):
    data = 0 # current sample records
    # we need to save the time that this sample is taken
    # time[current sample] = current time and number of samples
    # this needs to be static so that we don't just send the last sample
    # now increment for next sample
    # also we need to have a send limit, otherwise we will eventually run out of data
