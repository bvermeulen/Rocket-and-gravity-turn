import numpy as np
import rocket_equations

motor_isp = 335
mass_flow = 160               # kg / s
dry_mass = 17_000
fuel_mass = 40_000
drag_coefficient = 0.75
rocket_area = 1

rocket = rocket_equations.RocketPhysics(motor_isp, mass_flow, dry_mass, fuel_mass,
                                        drag_coefficient, rocket_area)

def test_atmosphere_Density():
    '''  Tests the function rocket.Atmosphere_Density for each thermocline '''

    density = rocket.atmosheric_density

    print(density(15_000))

    assert 1.225 == density(0)
    assert True == np.isclose(density(10_000),0.412707,1.0e-5)
    assert True == np.isclose(density(15_000),0.193669,1.0e-5)
    assert True == np.isclose(density(25_000),0.0394636,1.0e-6)
    assert True == np.isclose(density(35_000),0.00821081,1.0e-7)
    assert True == np.isclose(density(50_000),0.000979214,1.0e-8)
    assert True == np.isclose(density(60_000),0.000287784,1.0e-8)
    assert True == np.isclose(density(80_000),0.0000156489,1.0e-9)

def test_drag():
    ''' Tests the function rocket.Drag '''

    assert 4593.75 == rocket.drag(0, 100)