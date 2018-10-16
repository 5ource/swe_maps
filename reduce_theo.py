import numpy as np
from scipy.stats import ortho_group
from matplotlib import pyplot as plt
from funcDefines import getPrime

def rvs(dim=3):
    random_state = np.random
    H = np.eye(dim)
    D = np.ones((dim,))
    for n in range(1, dim):
        x = random_state.normal(size=(dim - n + 1,))
        D[n - 1] = np.sign(x[0])
        x[0] -= D[n - 1] * np.sqrt((x * x).sum())
        # Householder transformation
        Hx = (np.eye(dim - n + 1) - 2. * np.outer(x, x) / (x * x).sum())
        mat = np.eye(dim)
        mat[n - 1:, n - 1:] = Hx
        H = np.dot(H, mat)
        # Fix the last sign such that the determinant is 1
    D[-1] = (-1) ** (1 - (dim % 2)) * D.prod()
    # Equivalent to np.dot(np.diag(D), H) but faster, apparently
    H = (D * H.T).T
    return H

def reduce_ens(A, N=100):
    #initial A  size is   n x BN
    n, BN = np.shape(A)
    Aprime = getPrime(A)
    initSTD = np.std(Aprime, axis=1)    #we wish to conserve std
    #step 1: compute svd
    #U, Sig, Vt = np.linalg.svd(Aprime)  #too slow
    from sklearn.utils.extmath import randomized_svd
    U, Sig, Vt = randomized_svd(Aprime,
                                n_components=N,
                                n_iter=1,
                                random_state=None)
    #step 2: retain only 1st NxN quadrant of Sig
    SigNN = Sig[0:N] * 1/np.sqrt((BN+0.0)/N)        #it was already reduced! redundant
    print np.log10(Sig[0]/Sig[-1])
    V1T = ortho_group.rvs(dim=N)
    U = U[0:n, 0:N]
    Aprime = np.dot(U, np.dot(np.diag(SigNN), V1T))
    Aprime = getPrime(Aprime)
    Aprime = np.divide(np.multiply(Aprime, np.transpose([initSTD, ] * N)), np.transpose([np.std(Aprime, axis=1), ] *N))
    Anew    = Aprime + np.transpose([np.mean(A, 1), ] * N)

    # test to visualize if similar covariance
    if 0:
        K = 1000
        dim = n
        #randomly select K ensembles
        indexes = np.random.randint(0, dim, K)
        original_ens = A[indexes, :]
        reduced_ens  = Anew[indexes, :]
        original_cov = np.cov(original_ens)
        reduced_cov = np.cov(reduced_ens)
        M = np.max(original_cov)
        m = np.min(original_cov)
        visu = 1
        if visu == 1:
            plt.figure()
            plt.subplot(1, 3, 1)
            plt.imshow(original_cov, clim=[m, M])
            plt.title("original")
            plt.colorbar()
            plt.subplot(1, 3, 2)
            plt.imshow(reduced_cov, clim=[m, M])
            plt.title("reduced")
            plt.colorbar()
            plt.subplot(1, 3, 3)
            plt.imshow(reduced_cov - original_cov)
            plt.title("diff")
            plt.colorbar()
            #plt.savefig("dim_reduct_verification.png")
            plt.show()
        exit(0)

    return Anew


if 0:
    test = np.load("/Volumes/Untitled/zeshi/SWE/red_ens_Marg_ser_skip2_.npy") #, mmap_mode="r")
    test = test[np.std(test, axis=1) != 0, :]
    reduce_ens(test, 200)

