import argparse
import math
import time

import matplotlib.colors as colors
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import csr_matrix, save_npz

from dft import DFT


def desiredSize(n):
    p = int(math.log(n, 2))
    return int(pow(2, p+1))


def compress_image(im_fft, compression_level, originalCount):
    if compression_level < 0 or compression_level > 100:
        AssertionError('compression_level must be between 0 to 100')

    rest = 100 - compression_level
    lower = np.percentile(im_fft, rest//2)
    upper = np.percentile(im_fft, 100 - rest//2)
    print('non zero values for level {}% are {} out of {}'.format(compression_level, int(
        originalCount * ((100 - compression_level) / 100.0)), originalCount))

    compressed_im_fft = im_fft * \
        np.logical_or(im_fft <= lower, im_fft >= upper)
    save_npz('/matricies/coefficients-{}-compression.csr'.format(compression_level),
             csr_matrix(compressed_im_fft))

    return DFT.fast_two_dimension_inverse(compressed_im_fft)


def __main__():
    results = None
    try:
        results = parseArgs()
    except BaseException as e:
        print("ERROR\tIncorrect input syntax: Please check arguments and try again")
        return

    mode = results.mode
    image = results.image

    # run tests
    DFT.test()

    if mode == 1:
        # read the image
        im_raw = plt.imread(image).astype(float)

        # pad the image to desired size
        old_shape = im_raw.shape
        new_shape = desiredSize(old_shape[0]), desiredSize(old_shape[1])
        im = np.zeros(new_shape)
        im[:old_shape[0], :old_shape[1]] = im_raw

        # perform fft 2d
        fft_im = DFT.fast_two_dimension(im)

        # display
        fig, ax = plt.subplots(1, 2)
        ax[0].imshow(im[:old_shape[0], :old_shape[1]], plt.cm.gray)
        ax[0].set_title('original')
        ax[1].imshow(np.abs(fft_im), norm=colors.LogNorm())
        ax[1].set_title('fft 2d with lognorm')
        fig.suptitle('Mode 1')
        plt.show()

    elif mode == 2:
        # define a percentage keep fraction
        keep_fraction = 0.08

        # read the image
        im_raw = plt.imread(image).astype(float)

        # pad the image to desired size
        old_shape = im_raw.shape
        new_shape = desiredSize(old_shape[0]), desiredSize(old_shape[1])
        im = np.zeros(new_shape)
        im[:old_shape[0], :old_shape[1]] = im_raw

        # perform fft 2d and remove high frequency values
        fft_im = DFT.fast_two_dimension(im)
        r, c = fft_im.shape
        print("Fraction of pixels used {} and the number is ({}, {}) out of ({}, {})".format(
            keep_fraction, int(keep_fraction*r), int(keep_fraction*c), r, c))
        fft_im[int(r*keep_fraction):int(r*(1-keep_fraction))] = 0
        fft_im[:, int(c*keep_fraction):int(c*(1-keep_fraction))] = 0

        # perform ifft 2d to denoise the image
        denoised = DFT.fast_two_dimension_inverse(fft_im).real

        # display
        fig, ax = plt.subplots(1, 2)
        ax[0].imshow(im[:old_shape[0], :old_shape[1]], plt.cm.gray)
        ax[0].set_title('original')
        ax[1].imshow(denoised[:old_shape[0], :old_shape[1]], plt.cm.gray)
        ax[1].set_title('denoised')
        fig.suptitle('Mode 2')
        plt.show()
    elif mode == 3:
        # read the image
        im_raw = plt.imread(image).astype(float)

        # pad the image to desired size
        old_shape = im_raw.shape
        new_shape = desiredSize(old_shape[0]), desiredSize(old_shape[1])
        im = np.zeros(new_shape)
        im[:old_shape[0], :old_shape[1]] = im_raw
        originalCount = old_shape[0] * old_shape[1]

        # define compression levels
        compression = [0, 14, 30, 50, 70, 94]

        # write down abs of fft
        im_fft = DFT.fast_two_dimension(im)

        # render
        fig, ax = plt.subplots(2, 3)
        for i in range(2):
            for j in range(3):
                compression_level = compression[i*3 + j]
                im_compressed = compress_image(
                    im_fft, compression_level, originalCount)
                ax[i, j].imshow(np.real(im_compressed)[
                                :old_shape[0], :old_shape[1]], plt.cm.gray)
                ax[i, j].set_title('{}% compression'.format(compression_level))

        fig.suptitle('Mode 3')
        plt.show()
    elif mode == 4:
        # define sample runs
        runs = 10

        # run plots
        fig, ax = plt.subplots(1, 2)

        for algo_index, algo in enumerate([DFT.slow_two_dimension, DFT.fast_two_dimension]):
            print("starting measurement for {}".format(algo.__name__))
            x = []
            y = []

            power_2 = 2**5
            while power_2 <= 2**13:
                print("doing problem size of {}".format(power_2))
                a = np.random.rand(power_2, power_2)
                x.append(power_2)

                avg = 0
                for i in range(runs):
                    print("run {} ...".format(i+1))
                    start_time = time.time()
                    algo(a)
                    avg += time.time() - start_time

                avg /= runs
                y.append(avg)

                power_2 *= 2

            ax[algo_index].plot(x ,y)
            ax[algo_index].set_title(algo.__name__)
        fig.suptitle('Mode 4')
        plt.show()
    else:
        print("ERROR\tMode {} is not recofgnized".format(mode))
        return


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', action='store', dest='mode',
                        help='Mode of operation 1-> fast, 2-> denoise, 3-> compress&save 4-> plot', type=int, default=1)
    parser.add_argument('-i', action='store', dest='image',
                        help='image path to work on', type=str, default='moonlanding.png')
    return parser.parse_args()


if __name__ == "__main__":
    __main__()
