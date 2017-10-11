from voluptuous import Schema, ALLOW_EXTRA, All, Any, Required, Length, Object, Boolean, Range, Number, Coerce, IsFile, truth


@truth
def iscallable(f):
    return callable(f)


def validate(d):

    Vector3d = All(Any([Number(), Number(), Number()], (Number(), Number(), Number())), Length(min=3, max=3))

    base_schema = Schema(
        {
            'units': 'SI',
            'scale': Vector3d,
            Required('reference'): All(str, Length(min=1)),
            'partitioner': Any('metis', 'scotch', 'high order load balancing'),
            Required('safe', default=False): Boolean(),
            'initial': Any(str, {Required('name'): str, Required('func'): iscallable}),
            Required('restart', default=False): Boolean(),
            'restart casename': All(str, Length(min=1)),
            'restart ignore history': Boolean(),
            'preconditioner': {Required('factor'): Number()},
            Required('equations'):
                Any('euler', 'RANS', 'viscous', 'LES',
                    'DGviscous', 'DGRANS', 'DGeuler', 'DGMenterDES', 'DGLES'),
            'report': {Required('frequency'): All(Coerce(int), Range(min=1)),
                       'monitor': dict,
                       'forces': dict,
                       Required('Scale residuals by volume', default=False): Boolean()},
            'time marching': dict,
            'cell order': list,
            'Nodal Locations': {
                'Line': dict,
                'Tetrahedron': dict,
                'Tri': dict
            },
            Required('material', default='air'): All(str, Length(min=1)),
            'write output': {Required('frequency'): All(Coerce(int), Range(min=1)),
                             Required('format'): Any('none','vtk', 'ensight', 'native'),
                             Required('no volume vtk', default=False): Boolean(),
                             'surface variables': list,
                             'volume variables': list,
                             'surface interpolate': list,
                             'volume interpolate': list,
                             'start output real time cycle':
                                 All(Coerce(int), Range(min=0)),
                             'output real time cycle frequency':
                                 All(Coerce(int), Range(min=1)),
                             'variable_name_alias': dict,
                             'unsteady restart file output frequency': All(Coerce(int), Range(min=1))
                             },

        }, extra=ALLOW_EXTRA)

    d = base_schema(d)

    material_key = d['material']
    reference_key = d['reference']
    equations_key = d['equations']
    ic_keys = [key for key in d.keys() if key.startswith('IC_')]
    bc_keys = [key for key in d.keys() if key.startswith('BC_')]
    fz_keys = [key for key in d.keys() if key.startswith('FZ_')]

    material_schema = Schema(
        {
            Required('gamma', default=1.4): Number(),
            Required('gas constant', default=287.0): Number(),
            Required('Sutherlands const', default=110.4): Number(),
            Required('Prandtl No', default=0.72): Number(),
            Required('Turbulent Prandtl No', default=0.9): Number(),
            'gravity': Vector3d,
            'latitude': Number()
        })

    ic_schema = Schema(
        {
            'pressure': Number(),
            'temperature': Number(),
            'V': {
                'vector': Vector3d,
                'Mach': Number(),
            },
            'Reference Length': Number(),
            'Reynolds No': Number(),
            'turbulence intensity': Number(),
            'eddy viscosity ratio': Number(),
            'ambient turbulence intensity': Number(),
            'ambient eddy viscosity ratio': Number(),
            'location': Vector3d,
            'profile': {
                'ABL': {
                    'roughness length': Number(),
                    'friction velocity': Number(),
                    'surface layer height': Number(),
                    'Monin-Obukhov length': Number(),
                    'TKE': Number(),
                    'z0': Number(),
                },
                'field': All(str, IsFile()),
                'local profile': Boolean()
            },
            'static pressure ratio': Number(),
            'total pressure ratio': Number(),
            'total temperature ratio': Number(),
            'reference': str,
            'viscosity': Number()
        }, extra=ALLOW_EXTRA)

    timemarching_schema = Schema(
        {
            'unsteady': {
                'total time': Number(),
                'time step': Number(),
                'order': Any('first', 'second', 1, 2),
                'start': Coerce(int)
            },
            Required('scheme'): {
                'name': Any('euler', 'runge kutta',
                            'lu-sgs'),
                'stage': Any(1, 'rk third order tvd', 4, 5),
                'class': Object,
                'kind': Any('local timestepping', 'global timestepping'),
                'linear gradients': Boolean()
            },

            Required('lu-sgs', default={}): {
                Required('Include Backward Sweep', default=True): Boolean(),
                Required('Number Of SGS Cycles', default=8): All(Coerce(int), Range(min=1)),
                Required('Jacobian Epsilon', default=1.0e-8): Number(),
                Required('Include Relaxation', default=True): Boolean(),
                Required('Jacobian Update Frequency', default=1): All(Coerce(int), Range(min=1)),
                Required('Finite Difference Jacobian', default=False): Boolean(),
                Required('Use Rusanov Flux For Jacobian', default=True): Boolean()
            },

            Required('cfl'): Number(),
            'cfl transport': Number(),
            'cfl coarse': Number(),
            'cfl ramp factor': {
                Required('growth'): Number(),
                Required('initial'): Number()
            },
            'cfl transport for pmg levels' : list,
            'cfl for pmg levels' : list,
            'ramp func': iscallable,

            Required('cycles'): All(Coerce(int), Range(min=1)),

            'multigrid': All(Coerce(int), Range(min=1)),
            'multigrid cycles': All(Coerce(int), Range(min=1)),
            'multigrid ramp': Number(),
            'prolong factor': Number(),
            'prolong transport factor': Number(),

            Required('multipoly', default=False): Boolean(),
            'multipoly cycle pattern': list,
            'multipoly convect only': Boolean(),
            'multipoly relaxation': Number(),
            'High Order Filter Frequency': Coerce(int),
            'number of time step smoothing iterations': Coerce(int),

            Required('cfl viscous factor', default=1.0): Number()
        })

    fv_euler_schema = Schema(
        {
            Required('order'): Any('first', 'second', 'euler_second'),
            Required('limiter', default='vanalbada'): 'vanalbada',
            Required('precondition', default=False): Boolean()
        })

    viscous_schema = fv_euler_schema.extend(
        {
            Required('turbulence', default={}): {
                Required('les', default='none'): Any('none', 'WALE'),
            }
        })

    rans_schema = fv_euler_schema.extend(
        {
            Required('turbulence', default={}): {
                Required('model'): Any('sst', 'sas', 'sa-neg'),
                Required('les', default='none'): Any('none', 'DES', 'DDES', 'IDDES', 'SAS'),
                Required('betastar', default=0.09): Number(),
                'limit mut': Boolean(),
                'CDES_kw': Number(),
                'CDES_keps': Number(),
                'production': Coerce(int),
                'rotation correction': Boolean(),
                'CDES': Number()
            }
        })

    dg_euler_schema = Schema(
        {
            Required('order'): Any(0, 1, 2, 3, 4),
            Required('precondition', default=False): Boolean(),
            Required('c11 stability parameter', default=0.0): Number(),
            Required('c11 stability parameter transport', default=0.0): Number(),
            Required('LDG upwind parameter', default=0.5): Number(),
            'LDG upwind parameter aux': Number(),
            Required('Use MUSCL Reconstruction', default=False): Boolean(),
            'Approximate curved boundaries': Boolean(),
            'Filtering Cut-on Order': Coerce(int),
            'Filtering Epsilon': Coerce(int),
            'Filtering Strength': Coerce(int),
            'Inviscid Flux Scheme': Any('HLLC', 'Rusanov')
        })

    dg_viscous_schema = dg_euler_schema.extend(
        {
            Required('BR2 Diffusive Flux Scheme', default=False): Boolean(),
            'Shock Sensing': Boolean(),
            'Shock Sensing k': Number(),
            'Shock Sensing Viscosity Scale': Number(),
            'Shock Sensing Variable': Any('density', 'temperature', 'mach', 'turbulence')
        })

    dg_rans_schema = dg_euler_schema.extend(
        {
            Required('turbulence', default={}): {
                Required('model'): Any('sst', 'sas', 'sa-neg'),
                Required('les', default='none'): Any('none', 'DES', 'DDES', 'IDDES', 'SAS'),
                Required('betastar', default=0.09): Number(),
                'limit mut': Boolean(),
                'CDES_kw': Number(),
                'CDES_keps': Number(),
                'production': Coerce(int),
                'rotation correction': Boolean(),
                'CDES': Number()
            },
            Required('BR2 Diffusive Flux Scheme', default=False): Boolean(),
            Required('Use Rusanov for turbulence equations', default=False): Boolean(),
            'Shock Sensing': Boolean(),
            'Shock Sensing k': Number(),
            'Shock Sensing Viscosity Scale': Number(),
            'Shock Sensing Variable': Any('density', 'temperature', 'mach', 'turbulence')
        })

    equations_to_schema = {
        'euler': fv_euler_schema,
        'RANS': rans_schema,
        'viscous': viscous_schema,
        'LES': viscous_schema,
        'DGviscous': dg_viscous_schema,
        'DGRANS': dg_rans_schema,
        'DGeuler': dg_euler_schema,
        'DGMenterDES': dg_rans_schema,
        'DGLES': dg_rans_schema,
    }

    d[material_key] = material_schema(d.get(material_key, {}))
    d['time marching'] = timemarching_schema(d['time marching'])
    d[equations_key] = equations_to_schema[equations_key](d[equations_key])

    for k in ic_keys:
        d[k] = ic_schema(d[k])

    for k in bc_keys:
        pass

    for k in fz_keys:
        pass

    return d
