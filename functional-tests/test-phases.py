#!/usr/bin/env python
import sys
import numpy as np


def test_phases(file1, file2):
    fd1 = open(file1)
    fd2 = open(file1)

    for fd1_data, fd2_data in zip(fd1, fd2):
        fd1_data_eval = eval(fd1_data)
        fd2_data_eval = eval(fd2_data)

        assert np.isclose(fd1_data_eval['year'], fd2_data_eval['year'])
        assert np.isclose(fd1_data_eval['value'], fd2_data_eval['value'])


    fd1.close()
    fd2.close()

def main():
    test_phases(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
