import os
from hashlib import sha3_256, sha3_512, shake_128, shake_256
from polynomials import *
from modules import *
from ntt_helper import NTTHelperKyber
from numba import cuda,jit

try:
    from aes256_ctr_drbg import AES256_CTR_DRBG
except ImportError as e:
    print("Error importing AES CTR DRBG. Have you tried installing requirements?")
    print(f"ImportError: {e}\n")
    print("Kyber will work perfectly fine with system randomness")
    
    
DEFAULT_PARAMETERS = {
    "kyber_512" : {
        "n" : 256,
        "k" : 2,
        "q" : 3329,
        "eta_1" : 3,
        "eta_2" : 2,
        "du" : 10,
        "dv" : 4,
    },
    "kyber_768" : {
        "n" : 256,
        "k" : 3,
        "q" : 3329,
        "eta_1" : 2,
        "eta_2" : 2,
        "du" : 10,
        "dv" : 4,
    },
    "kyber_1024" : {
        "n" : 256,
        "k" : 4,
        "q" : 3329,
        "eta_1" : 2,
        "eta_2" : 2,
        "du" : 11,
        "dv" : 5,
    }
}

class Kyber:
    def __init__(self, parameter_set):
        self.n = parameter_set["n"]
        self.k = parameter_set["k"]
        self.q = parameter_set["q"]
        self.eta_1 = parameter_set["eta_1"]
        self.eta_2 = parameter_set["eta_2"]
        self.du = parameter_set["du"]
        self.dv = parameter_set["dv"]
        
        self.R = PolynomialRing(self.q, self.n, ntt_helper=NTTHelperKyber)
        self.M = Module(self.R)
        
        self.drbg = None
        self.random_bytes = os.urandom
        
    def set_drbg_seed(self, seed):
        """
        Setting the seed switches the entropy source
        from os.urandom to AES256 CTR DRBG
        
        Note: requires pycryptodome for AES impl.
        (Seemed overkill to code my own AES for Kyber)
        """
        self.drbg = AES256_CTR_DRBG(seed)
        self.random_bytes = self.drbg.random_bytes

    def reseed_drbg(self, seed):
        """
        Reseeds the DRBG, errors if a DRBG is not set.
        
        Note: requires pycryptodome for AES impl.
        (Seemed overkill to code my own AES for Kyber)
        """
        if self.drbg is None:
            raise Warning(f"Cannot reseed DRBG without first initialising. Try using `set_drbg_seed`")
        else:
            self.drbg.reseed(seed)
        
    @staticmethod
    def _xof(bytes32, a, b, length):
        """
        XOF: B^* x B x B -> B*
        """
        input_bytes = bytes32 + a + b
        if len(input_bytes) != 34:
            raise ValueError(f"Input bytes should be one 32 byte array and 2 single bytes.")
        return shake_128(input_bytes).digest(length)
        
    @staticmethod
    def _h(input_bytes):
        """
        H: B* -> B^32
        """
        return sha3_256(input_bytes).digest()
    
    @staticmethod  
    def _g(input_bytes):
        """
        G: B* -> B^32 x B^32
        """
        output = sha3_512(input_bytes).digest()
        return output[:32], output[32:]
    
    @staticmethod  
    def _prf(s, b, length):
        """
        PRF: B^32 x B -> B^*
        """
        input_bytes = s + b
        if len(input_bytes) != 33:
            raise ValueError(f"Input bytes should be one 32 byte array and one single byte.")
        return shake_256(input_bytes).digest(length)
    
    @staticmethod
    def _kdf(input_bytes, byte_length):
        """
        KDF: B^* -> B^*
        """
        return shake_256(input_bytes).digest(byte_length)
        
    def _generate_error_vector(self, sigma, eta, N, is_ntt=False):
        """
        Helper function which generates a element in the
        module from the Centered Binomial Distribution.
        """
        elements = []
        for i in range(self.k):
            input_bytes = self._prf(sigma,  bytes([N]), 64*eta)
            poly = self.R.cbd(input_bytes, eta, is_ntt=is_ntt)
            elements.append(poly)
            N = N + 1
        v = self.M(elements).transpose()
        return v, N
        
    def _generate_matrix_from_seed(self, rho, transpose=False, is_ntt=False):
        """
        Helper function which generates a element of size
        k x k from a seed `rho`.
        
        When `transpose` is set to True, the matrix A is
        built as the transpose.
        """
        A = []
        for i in range(self.k):
            row = []
            for j in range(self.k):
                if transpose:
                    input_bytes = self._xof(rho, bytes([i]), bytes([j]), 3*self.R.n)
                else:
                    input_bytes = self._xof(rho, bytes([j]), bytes([i]), 3*self.R.n)
                aij = self.R.parse(input_bytes, is_ntt=is_ntt)
                row.append(aij)
            A.append(row)
        return self.M(A)
        
    @staticmethod
    @cuda.jit
    def _cpapke_keygen_gpu(pk, sk, rho, sigma, A, s, e, t, result):
        """
        Algorithm 4 (Key Generation) - CUDA version
        """
        # Calculate the thread and block indices
        tx = cuda.threadIdx.x
        ty = cuda.blockIdx.x
        bw = cuda.blockDim.x

        # Shared memory for intermediate results
        shared_A = cuda.shared.array(shape=(k, k), dtype=int32)
        shared_s = cuda.shared.array(shape=(k,), dtype=int32)
        shared_e = cuda.shared.array(shape=(k,), dtype=int32)
        shared_t = cuda.shared.array(shape=(n,), dtype=int32)

        # Shared memory indices
        A_idx = tx
        s_idx = tx
        e_idx = tx
        t_idx = tx

        # Load data into shared memory
        for i in range(k):
            shared_s[i] = s[ty, i]
            shared_e[i] = e[ty, i]
            for j in range(k):
                shared_A[i, j] = A[ty, i, j]
            cuda.syncthreads()

        if tx < n:
            shared_t[tx] = 0

        cuda.syncthreads()

        # Construct the public key
        for i in range(k):
            for j in range(k):
                t_idx = tx
                if t_idx < n:
                    t_val = shared_t[t_idx] + shared_A[i, j] * shared_s[j]
                    shared_t[t_idx] = t_val
                cuda.syncthreads()

        for i in range(k):
            t_idx = tx
            if t_idx < n:
                t_val = shared_t[t_idx] + shared_e[i]
                shared_t[t_idx] = t_val
            cuda.syncthreads()

        # Reduce vectors mod^+ q
        for i in range(n):
            t_idx = tx
            if t_idx < n:
                t_val = shared_t[t_idx]
                shared_t[t_idx] = t_val % q
            cuda.syncthreads()

        # Encode elements to bytes
        for i in range(n):
            t_idx = tx
            if t_idx < n:
                result[ty, i] = t[t_idx].encode(l=12)

        if tx == 0:
            # Store rho in public key
            pk[ty] = rho
            # Store secret key in the result
            sk[ty] = s_idx, shared_s[s_idx].encode(l=12)
    @staticmethod
    @cuda.jit
    def _cpapke_enc_gpu(pk, m, coins, rho, eta_1, eta_2, du, dv, result):
        """
        Algorithm 5 (Encryption) - CUDA version
        """
        # Calculate the thread and block indices
        tx = cuda.threadIdx.x
        ty = cuda.blockIdx.x
        bw = cuda.blockDim.x

        # Shared memory for intermediate results
        shared_m_poly = cuda.shared.array(shape=(1,), dtype=int32)
        shared_r = cuda.shared.array(shape=(k,), dtype=int32)
        shared_e1 = cuda.shared.array(shape=(k,), dtype=int32)
        shared_u = cuda.shared.array(shape=(k,), dtype=int32)
        shared_v = cuda.shared.array(shape=(1,), dtype=int32)

        # Shared memory indices
        m_poly_idx = 0
        r_idx = tx
        e1_idx = tx
        u_idx = tx

        # Initialize shared memory
        if tx == 0:
            shared_m_poly[m_poly_idx] = m
            shared_v[0] = 0
        cuda.syncthreads()

        # Calculate N based on block index
        N = ty * bw * n

        # Load data into shared memory
        shared_r[r_idx], shared_e1[e1_idx] = 0, 0
        for i in range(k):
            shared_r[r_idx] = r[i]
            shared_e1[e1_idx] = e1[i]
            cuda.syncthreads()

        # Calculate At matrix elements
        At_elements = cuda.shared.array(shape=(k, k), dtype=int32)
        for i in range(k):
            for j in range(k):
                At_elements[i, j] = 0
                for m in range(n):
                    At_elements[i, j] += A[ty, i, j] * r[m]
                cuda.syncthreads()

        # Construct the public key
        for i in range(k):
            t_val = 0
            for j in range(k):
                t_val += At_elements[j, i] * shared_r[j]
            cuda.syncthreads()
            shared_u[u_idx] = t_val + shared_e1[u_idx]
            cuda.syncthreads()

        # Module/Polynomial arithmetic
        for i in range(du):
            for j in range(k):
                shared_v[0] += At_elements[j, i] * shared_r[j]
            cuda.syncthreads()
            shared_v[0] += shared_e1[u_idx]
            cuda.syncthreads()

        v = shared_v[0] + shared_m_poly[m_poly_idx]

        # Ciphertext to bytes
        c1 = shared_u[u_idx].compress(du).encode(l=du)
        c2 = v.compress(dv).encode(l=dv)

        # Store result in global memory
        result[ty, tx] = c1 + c2
    
    @staticmethod
    @cuda.jit
    def _cpapke_dec_gpu(sk, c, result):
        """
        Algorithm 6 (Decryption) - CUDA version
        """
        # Calculate the thread and block indices
        tx = cuda.threadIdx.x
        ty = cuda.blockIdx.x
        bw = cuda.blockDim.x

        # Define shared memory for u and v
        shared_u = cuda.shared.array(shape=(k, du), dtype=int32)
        shared_v = cuda.shared.array(shape=(dv,), dtype=int32)

        # Shared memory indices
        su_idx = tx
        sv_idx = tx

        # Load data into shared memory
        for i in range(du):
            shared_u[i, tx] = 0  # Initialize shared_u
        if tx < dv:
            shared_v[tx] = 0  # Initialize shared_v

        cuda.syncthreads()

        # Split ciphertext to vectors
        index = du * k * n // 8
        c2 = c[index:]

        # Recover the polynomial v
        for i in range(0, dv, bw):
            sv_idx = tx + i
            if sv_idx < dv:
                shared_v[sv_idx] = c2[sv_idx]

        cuda.syncthreads()

        # s_transpose (already in NTT form)
        st = sk[ty].from_ntt()

        # Decrypt u and accumulate v
        for i in range(du):
            su_idx = tx + i
            if su_idx < du:
                u_val = 0
                for j in range(k):
                    u_val += st[ty, j] * shared_u[i, j]

                # Store the result in shared memory
                shared_u[i, tx] = u_val
            cuda.syncthreads()

        cuda.syncthreads()

        # Recover message as polynomial
        m = 0
        for i in range(du):
            su_idx = tx + i
            if su_idx < du:
                m += shared_u[i, tx]
        m = shared_v[tx] - m

        # Return message as bytes
        if tx == 0:
            result[ty] = m.compress(1).encode(l=1)
    
# Initialise with default parameters for easy import
Kyber512 = Kyber(DEFAULT_PARAMETERS["kyber_512"])
Kyber768 = Kyber(DEFAULT_PARAMETERS["kyber_768"])
Kyber1024 = Kyber(DEFAULT_PARAMETERS["kyber_1024"])
    
