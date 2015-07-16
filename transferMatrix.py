import numpy


class TransferMatrix:
    """
        Dielectric layer TMM

        How the functions eat structure matricies:

        | T |   |        | |        | |     |   | 1 |
        |   | = | Bottom | | Matrix | | Top | = |   |
        | 0 |   |        | |        | |     |   | R |

    """

    @staticmethod
    def structure(*args):
        """
           args - separate structure matricies
           Left to Right = Bottom to Top
        """
        mat = numpy.identity(2, dtype=numpy.complex64)
        for m in args:
            mat = numpy.dot(m.matrix, mat)
        return TransferMatrix(mat)

    @staticmethod
    def layer(n, d, wavelength):
        """
            Creates a Air-DielectricLayer-Air Transfer Matrix
        """
        bottomBoundary = numpy.array([[(1+n)/(2*n), (n-1)/(2*n)], [(n-1)/(2*n), (1+n)/(2*n)]], dtype=numpy.complex64)
        topBoundary = numpy.array([[(1+n)/2, -(n-1)/2], [-(n-1)/2, (1+n)/2]], dtype=numpy.complex64)
        propagation = numpy.array([[numpy.exp(-1j*n*d*2*numpy.pi/wavelength), 0],
                                   [0, numpy.exp(1j*n*d*2*numpy.pi/wavelength)]], dtype=numpy.complex64)

        return TransferMatrix.structure(TransferMatrix(bottomBoundary),
                                        TransferMatrix(propagation),
                                        TransferMatrix(topBoundary))

    @staticmethod
    def boundingLayer(n1, n2):
        """
            Creates a DielectricLayer-DielectricLayer Boundary Transfer Matrix
        """
        leftBoundary = numpy.array([[(n1+n2)/(2*n2), (n2-n1)/(2*n2)],
                                    [(n2-n1)/(2*n2), (n1+n2)/(2*n2)]], dtype=numpy.complex64)
        return TransferMatrix(leftBoundary)

    @staticmethod
    def propagationLayer(n, d, wavelength):
        """
            Creates a Propagation Transfer Matrix, width d, refractive index n
        """
        propagation = numpy.array([[numpy.exp(-1j*n*d*2*numpy.pi/wavelength), 0],
                                   [0, numpy.exp(1j*n*d*2*numpy.pi/wavelength)]], dtype=numpy.complex64)
        return TransferMatrix(propagation)

    def __init__(self, matrix):
        self.matrix = matrix

    def invert(self):
        self.matrix = numpy.linalg.inv(self.matrix)

    def appendLeft(self, matrix):
        self.matrix = numpy.dot(matrix.matrix, self.matrix)

    def appendRight(self, matrix):
        self.matrix = numpy.dot(self.matrix, matrix.matrix)

def solvePropagation(transferMatrix, incidentField=1.0):
    """Calculate reflectance and transmittance"""
    # res[1] = transmittance, res[0] = reflectance
    lhs = numpy.array([[transferMatrix.matrix[0, 1], -1],
                      [transferMatrix.matrix[1, 1], 0]])
    rhs = numpy.array([-transferMatrix.matrix[0, 0], -transferMatrix.matrix[1, 0]])
    rhs = numpy.multiply(rhs, incidentField)
    res = numpy.linalg.solve(lhs, rhs)
    reflectance = res[0]
    transmittance = res[1]
    return reflectance, transmittance

def findReciprocalTransferMatrix(transmittance, reflectance, bottomMat=TransferMatrix(numpy.identity(2)),
                       topMat=TransferMatrix(numpy.identity(2))):  # , incidentField=1.0
    assert transmittance != 0

    matrix = numpy.array([[1/numpy.conj(transmittance), reflectance/transmittance],
                         [numpy.conj(reflectance/transmittance), 1/transmittance]])
    matrix = numpy.dot(numpy.linalg.inv(bottomMat.matrix), matrix)
    matrix = numpy.dot(matrix, numpy.linalg.inv(topMat.matrix))
    return TransferMatrix(matrix)

def findReciprocalTransferMatrixLegacy(transmittance, reflectance, bottomMat=TransferMatrix(numpy.identity(2)),
                       topMat=TransferMatrix(numpy.identity(2))):  # , incidentField=1.0
    a = numpy.identity(2)
    b = numpy.array([[numpy.real(reflectance), numpy.imag(reflectance)],
                    [numpy.imag(reflectance), -numpy.real(reflectance)]])
    lhs = numpy.vstack((numpy.hstack((a, b)), numpy.hstack((b, a))))
    rhs = numpy.array([numpy.real(transmittance), numpy.imag(transmittance), 0, 0])
    res = numpy.linalg.solve(lhs, rhs)
    matrix = numpy.array([[res[0]+1j*res[1], res[2]-1j*res[3]],
              [res[2]+1j*res[3], res[0]-1j*res[1]]])

    matrix = numpy.dot(numpy.linalg.inv(bottomMat.matrix), matrix)
    matrix = numpy.dot(matrix, numpy.linalg.inv(topMat.matrix))
    return TransferMatrix(matrix)

def findGeneralizedTransferMatrix(transmitance1, reflectance1, transmitance2, reflectance2,
                                  bottomMat1=TransferMatrix(numpy.identity(2)), topMat1=TransferMatrix(numpy.identity(2)),
                                  bottomMat2=TransferMatrix(numpy.identity(2)), topMat2=TransferMatrix(numpy.identity(2))):
    a12 = numpy.dot(numpy.linalg.inv(bottomMat1.matrix), numpy.array([[transmitance1], [0]]))
    a34 = numpy.dot(numpy.linalg.inv(bottomMat2.matrix), numpy.array([[transmitance2], [0]]))

    b12 = numpy.dot(topMat1.matrix, numpy.array([[1], [reflectance1]]))
    b34 = numpy.dot(topMat2.matrix, numpy.array([[1], [reflectance2]]))

    rhs = numpy.array([a12[0, 0], a34[0, 0], a12[1, 0], a34[1, 0]])

    bmat = numpy.array([[b12[0, 0], b12[1, 0]],
                        [b34[0, 0], b34[1, 0]]])

    lhs = numpy.vstack((numpy.hstack((bmat, numpy.zeros((2, 2)))),
                        numpy.hstack((numpy.zeros((2, 2)), bmat))))
    res = numpy.linalg.solve(lhs, rhs)

    mat = numpy.array([[res[0], res[2]],
                      [res[1], res[3]]])
    return TransferMatrix(mat)
