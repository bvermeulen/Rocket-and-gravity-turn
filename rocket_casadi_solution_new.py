# Based on:
# Gravity Turn Maneuver with direct multiple shooting using CVodes
# (c) Mirko Hahn
# https://mintoc.de/index.php/Gravity_Turn_Maneuver_(Casadi)
# https://github.com/zegkljan/kos-stuff/tree/master/non-kos-tools/gturn
# ----------------------------------------------------------------
import casadi as cs
import numpy
from pprint import pprint


# noinspection PyPep8Naming
def compute_gravity_turn(m0, m1, g0, r0, Isp0, Isp1, Fmax, cd, A, H, rho, h_obj,
                         v_obj, q_obj, N=300, vel_eps=1e-3):
    '''
    Computes gravity turn profile
    :params:
        m0: wet (launch) mass (kg)
        m1: dry mass (kg)
        g0: gravitational acceleration at zero altitude (m * s^-2)
        r0: "orbit" radius at zero altitude (body radius) (m)
        Isp0: specific impulse of the engine(s) at zero altitude (s)
        Isp1: specific impulse of the engine(s) in vacuum (s)
        Fmax: maximum thrust of the engine(s) (N)
        cd: drag coefficient
        A: reference area of the vehicle (m^2)
        H: scale height of the atmosphere (m)
        rho: density of the atmosphere at zero altitude (kg * m^-3)
        h_obj: target altitude (m)
        v_obj: target velocity (m * s^-1)
        q_obj: target angle to vertical (rad)
        N: number of shooting interval
        vel_eps: initial velocity (must be nonzero, e.g. a very small number)
        (m * s^-1)
    :return:
        a dictionary with results
    '''
    # Create symbolic variables
    x = cs.SX.sym('[m, v, q, h, d]')  # Vehicle state
    u = cs.SX.sym('u')  # Vehicle controls
    T = cs.SX.sym('T')  # Time horizon (s)

    # Introduce symbolic expressions for important composite terms
    Fthrust = Fmax * u
    Fdrag = 0.5 * A * cd * rho * cs.exp(-x[3] / H) * x[1] ** 2
    r = x[3] + r0
    g = g0 * (r0 / r) ** 2
    vhor = x[1] * cs.sin(x[2])
    vver = x[1] * cs.cos(x[2])
    Isp = Isp1 + (Isp0 - Isp1) * cs.exp(-x[3] / H)

    # Build symbolic expressions for ODE right hand side
    mdot = -(Fthrust / (Isp * g0))
    vdot = (Fthrust - Fdrag) / x[0] - g * cs.cos(x[2])
    hdot = vver
    ddot = vhor / r
    qdot = g * cs.sin(x[2]) / x[1] - ddot

    # Build the DAE function
    ode = [
        mdot,
        vdot,
        qdot,
        hdot,
        ddot
    ]
    quad = u
    dae = {'x': x,
           'p': cs.vertcat(u, T),
           'ode': T * cs.vertcat(*ode),
           'quad': T * quad}
    I = cs.integrator('I', 'cvodes', dae,
                      {'t0': 0.0,
                       'tf': 1.0 / N,
                       'nonlinear_solver_iteration': 'functional'
                       })

    # Specify upper and lower bounds as well as initial values for DAE
    # parameters, states and controls
    p_min = [0.0]
    p_max = [600.0]
    p_init = [300.0]

    u_min = [0.0]
    u_max = [1.0]
    u_init = [0.5]

    x0_min = [m0, vel_eps, 0.0, 0.0, 0.0]
    x0_max = [m0, vel_eps, 0.5 * cs.pi, 0.0, 0.0]
    x0_init = [m0, vel_eps, 0.05 * cs.pi, 0.0, 0.0]

    xf_min = [m1, v_obj, q_obj, h_obj, 0.0]
    xf_max = [m0, v_obj, q_obj, h_obj, cs.inf]
    xf_init = [m1, v_obj, q_obj, h_obj, 0.0]

    x_min = [m1, vel_eps, 0.0, 0.0, 0.0]
    x_max = [m0, cs.inf, cs.pi, cs.inf, cs.inf]
    x_init = [0.5 * (m0 + m1), 0.5 * v_obj, 0.5 * q_obj, 0.5 * h_obj, 0.0]

    # Useful variable block sizes
    np = 1  # Number of parameters
    nx = x.size1()  # Number of states
    nu = u.size1()  # Number of controls
    ns = nx + nu  # Number of variables per shooting interval

    # Introduce symbolic variables and disassemble them into blocks
    V = cs.MX.sym('X', N * ns + nx + np)
    P = V[0]
    X = [V[(np + i * ns):(np + i * ns + nx)] for i in range(0, N + 1)]
    U = [V[(np + i * ns + nx):(np + (i + 1) * ns)] for i in range(0, N)]

    # Nonlinear constraints and Lagrange objective
    G = []
    F = 0.0

    # Build DMS structure
    x0 = p_init + x0_init
    for i in range(0, N):
        Y = I(x0=X[i], p=cs.vertcat(U[i], P))
        G += [Y['xf'] - X[i + 1]]
        F = F + Y['qf']

        frac = float(i + 1) / N
        x0 = x0 + u_init + [x0_init[i] + frac * (xf_init[i] - x0_init[i])
                            for i in range(0, nx)]

    # Lower and upper bounds for solver
    lbg = 0.0
    ubg = 0.0
    lbx = p_min + x0_min + u_min + (N - 1) * (x_min + u_min) + xf_min
    ubx = p_max + x0_max + u_max + (N - 1) * (x_max + u_max) + xf_max

    # Solve the problem using IPOPT
    nlp = {'x': V, 'f': (m0 - X[-1][0]) / (m0 - m1), 'g': cs.vertcat(*G)}
    S = cs.nlpsol('S', 'ipopt', nlp, {'ipopt': {'tol': 1e-4,
                                                'print_level': 5,
                                                'max_iter': 500}})
    r = S(x0=x0,
          lbx=lbx,
          ubx=ubx,
          lbg=lbg,
          ubg=ubg)
    print('RESULT: {}'.format(S.stats()['return_status']))
    if S.stats()['return_status'] in {'Invalid_Number_Detected'}:
        return None
    # Extract state sequences and parameters from result
    x = r['x']
    f = r['f']
    T = float(x[0])

    t = numpy.linspace(0, T, N + 1)
    m = numpy.array(x[np::ns]).squeeze()
    v = numpy.array(x[np + 1::ns]).squeeze()
    q = numpy.array(x[np + 2::ns]).squeeze()
    h = numpy.array(x[np + 3::ns]).squeeze()
    d = numpy.array(x[np + 4::ns]).squeeze()
    u = numpy.concatenate((numpy.array(x[np + nx::ns]).squeeze(), [0.0]))
    return {'time': t,
            'mass': m,
            'speed': v,
            'altitude': h,
            'control': u,
            'body_curvature': d,
            'vertical_angle': q}

def main():
    # Artificial model parameters
    N = 300                   # Number of shooting intervals
    vel_eps = 1e-3            # Initial velocity (km/s)

    # Vehicle parameters
    m0   = 11_300                      # Launch mass (kg)
    m1   = 1_300                       # Dry mass (kg)
    g0   = 9.81                        # Gravitational acceleration at altitude zero (m/s^2)
    r0   = 6_000_000                   # Radius at altitude zero (m)
    Isp0 = 300.0                       # Specific impulse at zero altude (s)
    Isp1 = 300.0                       # Specific impulse at vacuum (s)
    Fmax = 600_000                     # Maximum thrust (N)

    # Atmospheric parameters
    cd  = 0.021                        # Drag coefficients
    A   = 1.0                          # Reference area (m^2)
    H   = 5600                         # Scale height (m)
    rho = (1.0 * 1.2230948554874)      # Density at altitude zero

    # Target orbit parameters
    h_obj = 75000                      # Target altitude (m)
    v_obj = 2287                       # Target velocity (m/s)
    q_obj = 0.5 * cs.pi                # Target angle to vertical (rad)

    result = compute_gravity_turn(
        m0, m1, g0, r0, Isp0, Isp1, Fmax, cd, A, H, rho, h_obj,
        v_obj, q_obj, N=N, vel_eps=vel_eps)

    pprint(result)

if __name__ == '__main__':
    main()