'''
Based on:
  Gravity Turn Maneuver with direct multiple shooting using CVodes
  (c) Mirko Hahn
  https://mintoc.de/index.php/Gravity_Turn_Maneuver_(Casadi)
  https://github.com/zegkljan/kos-stuff/tree/master/non-kos-tools/gturn
----------------------------------------------------------------
'''
import sys
from pathlib import Path
import casadi as cs
import numpy as np
import pandas as pd
from rocket_input import read_rocket_config


# noinspection PyPep8Naming
def compute_gravity_turn(m0, m1, g0, r0, Isp0, Isp1, Fmax, cd, A, H, rho, h_obj,
                         v_obj, q_obj, N=300, vel_eps=1e-3):
    '''
    Computes gravity turn profile
    :params:
        m0: wet (launch) mass (kg or ton)
        m1: dry mass (kg or ton)
        g0: gravitational acceleration at zero altitude (m * s^-2 or km * s^-2)
        r0: "orbit" radius at zero altitude (body radius) (m or km)
        Isp0: specific impulse of the engine(s) at zero altitude (s)
        Isp1: specific impulse of the engine(s) in vacuum (s)
        Fmax: maximum thrust of the engine(s) (N or MN)
        cd: drag coefficient
        A: reference area of the vehicle (m^2)
        H: scale height of the atmosphere (m or km)
        rho: density of the atmosphere at zero altitude (kg * m^-3)
        h_obj: target altitude (m or km)
        v_obj: target velocity (m * s^-1 of km * s^-1)
        q_obj: target angle to vertical (rad)
        N: number of shooting interval
        vel_eps: initial velocity (must be nonzero, e.g. a very small number)
        (m * s^-1 or km * s^-1)

    :returns:
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
    ode = [mdot, vdot, qdot, hdot, ddot]
    quad = u
    dae = {'x': x, 'p': cs.vertcat(u, T), 'ode': T * cs.vertcat(*ode), 'quad': T * quad}
    I = cs.integrator(
        'I', 'cvodes', dae,
        {'t0': 0.0, 'tf': 1.0 / N, 'nonlinear_solver_iteration': 'functional'}
    )

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
    npars = 1  # Number of parameters
    nx = x.size1()  # Number of states
    nu = u.size1()  # Number of controls
    ns = nx + nu    # Number of variables per shooting interval

    # Introduce symbolic variables and disassemble them into blocks
    V = cs.MX.sym('X', N * ns + nx + npars)
    P = V[0]
    X = [V[(npars + i * ns):(npars + i * ns + nx)] for i in range(0, N + 1)]
    U = [V[(npars + i * ns + nx):(npars + (i + 1) * ns)] for i in range(0, N)]

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
    S = cs.nlpsol(
        'S', 'ipopt', nlp, {'ipopt': {'tol': 1e-4, 'print_level': 5, 'max_iter': 500}}
    )
    r = S(x0=x0, lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg)
    print('RESULT: {}'.format(S.stats()['return_status']))
    if S.stats()['return_status'] in {'Invalid_Number_Detected'}:
        return None
    # Extract state sequences and parameters from result
    x = r['x']
    f = r['f']
    T = float(x[0])

    t = np.linspace(0, T, N + 1)
    m = np.array(x[npars::ns]).squeeze()
    v = np.array(x[npars + 1::ns]).squeeze()
    q = np.array(x[npars + 2::ns]).squeeze()
    h = np.array(x[npars + 3::ns]).squeeze()
    d = np.array(x[npars + 4::ns]).squeeze()
    u = np.concatenate((np.array(x[npars + nx::ns]).squeeze(), [0.0]))

    return {
        'time': t,
        'mass': m,
        'vel': v,
        'alt': h,
        'control': u,
        'hor_angle': d,
        'ver_angle': q
    }


def main(config_file):
    (   rocket_params,
        environment_params,
        model_params,
        io_params
    ) = read_rocket_config(config_file)

    # Vehicle parameters
    m0   = (rocket_params.fuel_mass +
            rocket_params.dry_mass)           # Launch mass (kg or ton)
    m1   = rocket_params.dry_mass             # Dry mass (kg or ton)
    Isp0 = rocket_params.motor_isp0           # Specific impulse at zero altude (s)
    Isp1 = rocket_params.motor_isp1           # Specific impulse at vacuum (s)
    A    = rocket_params.rocket_area          # Reference area (m^2)
    Fmax = rocket_params.max_thrust           # Maximum thrust (N or MN)
    vel_eps = rocket_params.vel               # Initial velocity (m/s or km/s)

    # Environmental parameters
    g0  = environment_params.gravity          # Gravitational acceleration at altitude zero (m/s^2 or km/s^2)
    r0  = environment_params.radius           # Radius at altitude zero (m or km)
    cd  = environment_params.drag_coefficient # Drag coefficients
    H   = environment_params.scale_height     # Scale height (m or km)
    rho = environment_params.density          # Density at altitude zero (x 1000)

    # Model and target orbit parameters
    N     = model_params.N                    # Number of shooting intervals
    h_obj = model_params.h_obj                # Target altitude (m or km)
    v_obj = model_params.v_obj                # Target velocity (m/s or km/s)
    q_obj = model_params.q_obj / 180 * cs.pi  # Target angle to vertical (rad)

    # output file
    model_file = model_params.model_file

    result = compute_gravity_turn(
        m0, m1, g0, r0, Isp0, Isp1, Fmax,
        cd, A, H, rho, h_obj,
        v_obj, q_obj, N=N, vel_eps=vel_eps
    )

    result_df = pd.DataFrame(result)
    result_df.to_excel(model_file, index=False)
    print(result_df.head())


if __name__ == '__main__':
    config_file_name = 'None'
    if len(sys.argv) == 2:
        config_file_name = sys.argv[1]

    config_file_name = Path(config_file_name)
    if not config_file_name.is_file():
        print(f'incorrect config file: {config_file_name}')
        exit()

    main(config_file_name)