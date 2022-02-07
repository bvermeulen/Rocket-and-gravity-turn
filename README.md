# Rocket
A rocket launch simulation using a gravity turn maneuver using differential equations as described by Mintoc 
https://mintoc.de/index.php/Gravity_Turn_Maneuver (see below for further explanation). 
The Casadi solution is based on the code given in 
https://mintoc.de/index.php/Gravity_Turn_Maneuver_(Casadi), updated by Mirko Hahn in the github repository 
https://github.com/zegkljan/kos-stuff/tree/master/non-kos-tools/gturn. 

After setting up the environment, run the programs as follows:

Calculation of the thrust control:
```
python rocket_casadi_solution.py mintoc_20T_1.cfg
```
This program will create an excel trhust contril file as defined in the config file. Then run the launch program using this thrust control solution
```
python rocket_launch.py mintoc_20T_1.cfg
```
Where the configuration file `mintoc_20T_1.cfg` is
```
# parameter must be given in this order
rocket dry mass (kg)           m_dry  : 2_000
rocket fuel mass (kg)          m_fuel : 20_000
motor impulse (s) zero alt     Isp0   : 450
motor impulse (s) vacuum       Isp1   : 450
maximum thrust (N)             Fmax   : 600_000
rocket reference area (m^2)    A      : 3.5
initial velocity (m / s)       vel    : 1e-3
initial flight angle (radians) beta   : 0.000274
initial altitude (m)           h      : 0
gravity at zero altitude       g0     : 9.81
radius at altitude zero        r0     : 6_000_000
drag coefficient (_)           cd     : 0.75
scale height (m)               H      : 8_500
density at zero altitude       rho    : 1.2230948554874
number of shooting intervals   N      : 300
altitude objective (m)         h_obj  : 200_000
velocity objective (m/s)       v_obj  : 8_000
beta objective (degrees)       q_obj  : 90
control file (.xlsx)                  : mintoc_gravity_turn_20T_1.xlsx
time interval (s)  1.1268             : 1
status_update_step                    : 120
duration (s)                          : 20_000
speed min_max (m/s)                   : 0, 10_000
flight angle min max (degrees)        : 0, 110
altitude min max (m)                  : 0, 2_000_000
h_range min max (degrees)             : 0, 1440
acceleration min max (m*s-2)          : -100, 170
rocket sprite file                    : rocket_sprite2.png
```
The code is tested for Python 3.10. 

Once the program starts it gives main parameters in the console and a display of graphs and trajectory.

<img src="rocket_launch.png" alt="rocket" width="70%" />

# Gravity turn

The gravity turn or zero lift turn is a common maneuver used to launch spacecraft into orbit from bodies that have non-negligible atmospheres. The goal of the maneuver is to minimize atmospheric drag by always orienting the vehicle along the velocity vector. In this maneuver, the vehicle's pitch is determined solely by the change of the velocity vector through gravitational acceleration and thrust. The goal is to find a launch configuration and thrust control strategy that achieves a specific orbit with minimal fuel consumption. 

**Physical description and model derivation**

For the purposes of this model, we start with the following ODE system proposed by Culler et. al. in [Culler1957]:

<img src="https://render.githubusercontent.com/render/math?math=\dot{v} = \frac{F}{m} - g \cdot \cos \beta">
<img src="https://render.githubusercontent.com/render/math?math=v\dot{\beta} = g \cdot \sin{\beta}"> 

where v is the speed of the vehicle, g is the gravitational acceleration at the vehicle's current altitude, F is the accelerating force and &beta; is the angle between the vertical and the vehicle's velocity vector. In the original version of the model, the authors neglect aspects of the problem:
- Variation of g over altitude
- Decrease of vehicle mass due to fuel consumption
- Curvature of the surface
- Atmospheric drag

**Changes in gravitational acceleration**

To account for changes in g, we make the following substitution:

<img src="https://render.githubusercontent.com/render/math?math=g = g_0 \cdot \left(\frac{r_0}{r_0 %2B h}\right)^2"> 

where g<sub>0</sub> is the gravitational acceleration at altitude zero and r<sub>0</sub> is the distance of altitude zero from the center of the reference body.

**Decrease in vehicle mass**

To account for changes in vehicle mass, we consider m a differential state with the following derivative:

<img src="https://render.githubusercontent.com/render/math?math=\dot{m} = -\frac{F}{I_{sp} \cdot g_0}">

where I<sub>sp</sub> is the specific impulse of the vehicle's engine. Specific impulse is a measure of engine efficiency. For rocket engines, it directly correlates with the engine's exhaust velocity and may vary with atmospheric pressure, velocity, engine temperature and combustion dynamics. For the purposes of this model, we will assume it to be constant.

The vehicle's fuel reserve is modelled by two parameters: m<sub>0</sub> denotes the launch mass (with fuel) and m<sub>1</sub> denotes the dry mass (without fuel).

**Curvature of the reference body's surface**

To accomodate the reference body's curvature, we introduce an additional differential state &theta which represents the change in the vehicle's polar angle with respect to the launch site. The derivative is given by

<img src="https://render.githubusercontent.com/render/math?math=\dot{\theta} = \frac{v \cdot \sin \beta}{r_0 %2B h}"> 

Note that the vertical changes as the vehicle moves around the reference body meaning that the derivative of &beta; must be changed as well:

<img src="https://render.githubusercontent.com/render/math?math=\dot{\beta} = \frac{g \cdot \sin{\beta}}{v} - \frac{v \cdot \sin \beta}{r_0 %2B h}">. 

**Atmospheric drag**

To model atmospheric drag, we assume that the vehicles draf coefficient c<sub>d</sub> is constant. The drag force is given by

<img src="https://render.githubusercontent.com/render/math?math=F_{drag} = \frac{1}{2} \rho A c_d v^2"> 

where &rho; is the density of the atmosphere and A is the vehicle's reference area. We assume that atmospheric density decays exponentially with altitude:

<img src="https://render.githubusercontent.com/render/math?math=\rho = \rho_0 \cdot e^{-\frac{h}{H}}"> 

where &rho<sub>0</sub> is the atmospheric density at altitude zero and H is the scale height of the atmosphere. The [drag force] is introduced into the acceleration term:

<img src="https://render.githubusercontent.com/render/math?math=\dot{v} = \frac{F - F_{drag}}{m} - g \cdot \cos \beta">. 

Note that if the vehicle is axially symmetric and oriented in such a way that its symmetry axis is parallel to the velocity vector, it does not experience any lift forces. This model is simplified. It does not account for changes in temperature and atmospheric composition with altitude. Also, c<sub>d</sub> varies with fluid viscosity and vehicle velocity. Specifically, drastic changes in c<sub>d</sub> occur as the vehicle breaks the sound barrier. This is not accounted for in this model. 
