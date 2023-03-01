import numbers
import numpy as np
from src.model_construction.generic_technology_constraints import *
import src.model_construction as mc
import src.config_model as m_config



def add_technologies(nodename, set_tecsToAdd, model, data, b_node):
    r"""
    Adds all technologies as model blocks to respective node.

    This function initializes parameters and decision variables for all technologies at respective node.
    For each technology, it adds one block indexed by the set of all technologies at the node :math:`S_n`.
    This function adds Sets, Parameters, Variables and Constraints that are common for all technologies.
    For each technology type, individual parts are added. The following technology types are currently available:

    - Type RES: Renewable technology with cap_factor as input. Constructed with \
      :func:`src.model_construction.generic_technology_constraints.constraints_tec_RES`
    - Type CONV1: n inputs -> n output, fuel and output substitution. Constructed with \
      :func:`src.model_construction.generic_technology_constraints.constraints_tec_CONV1`
    - Type CONV2: n inputs -> n output, fuel substitution. Constructed with \
      :func:`src.model_construction.generic_technology_constraints.constraints_tec_CONV2`
    - Type CONV2: n inputs -> n output, no fuel and output substitution. Constructed with \
      :func:`src.model_construction.generic_technology_constraints.constraints_tec_CONV3`
    - Type STOR: Storage technology (1 input -> 1 output). Constructed with \
      :func:`src.model_construction.generic_technology_constraints.constraints_tec_STOR`

    The following description is true for new technologies. For existing technologies a few adaptions are made
    (see below).

    **Set declarations:**

    - Set of input carriers
    - Set of output carriers

    **Parameter declarations:**

    - Min Size
    - Max Size
    - Output max (same as size max)
    - Unit CAPEX (annualized from given data on up-front CAPEX, lifetime and discount rate)
    - Variable OPEX
    - Fixed OPEX

    **Variable declarations:**

    - Size (can be integer or continuous)
    - Input for each input carrier
    - Output for each output carrier
    - CAPEX
    - Variable OPEX
    - Fixed OPEX

    **Constraint declarations**
    - CAPEX, can be linear (for ``capex_model == 1``) or piecewise linear (for ``capex_model == 2``). Linear is defined as:

    .. math::
        CAPEX_{tec} = Size_{tec} * UnitCost_{tec}

    - Variable OPEX: defined per unit of output for the main carrier:

    .. math::
        OPEXvar_{t, tec} = Output_{t, maincarrier} * opex_{var} \forall t \in T

    - Fixed OPEX: defined as a fraction of annual CAPEX:

    .. math::
        OPEXfix_{tec} = CAPEX_{tec} * opex_{fix}

    Existing technologies, i.e. existing = 1, can be decommissioned (decommission = 1) or not (decommission = 0).
    For technologies that cannot be decommissioned, the size is fixed to the size given in the technology data.
    For technologies that can be decommissioned, the size can be smaller or equal to the initial size. Reducing the
    size comes at the decommissioning costs specified in the economics of the technology.
    The fixed opex is calculated by determining the capex that the technology would have costed if newly build and
    then taking the respective opex_fixed share of this. This is done with the auxiliary variable var_capex_aux.

    :param str nodename: name of node for which technology is installed
    :param object b_node: pyomo block for respective node
    :param object model: pyomo model
    :param DataHandle data:  instance of a DataHandle
    :return: model
    """
    def init_technology_block(b_tec, tec):

        # TECHNOLOGY DATA
        tec_data = data.technology_data[nodename][tec]
        technology_model = tec_data.technology_model
        existing = tec_data.existing
        decommission = tec_data.decommission
        size_is_int = tec_data.size_is_int
        size_min = tec_data.size_min
        size_max = tec_data.size_max
        economics = tec_data.economics
        performance_data = tec_data.performance_data
        if existing:
            size_initial = tec_data.size_initial
            size_max = size_initial

        # SIZE
        if size_is_int:
            unit_size = u.dimensionless
        else:
            unit_size = u.MW
        b_tec.para_size_min = Param(domain=NonNegativeReals, initialize=size_min, units=unit_size)
        b_tec.para_size_max = Param(domain=NonNegativeReals, initialize=size_max, units=unit_size)

        if existing:
            b_tec.var_size_initial = Param(within=NonNegativeReals, initialize=size_initial, units=unit_size)

        if existing and not decommission:
            # Decommissioning is not possible, size fixed
            b_tec.var_size = Param(within=NonNegativeReals, initialize=b_tec.var_size_initial, units=unit_size)
        else:
            # Decommissioning is possible, size variable
            if size_is_int:
                b_tec.var_size = Var(within=NonNegativeIntegers, bounds=(b_tec.para_size_min, b_tec.para_size_max))
            else:
                b_tec.var_size = Var(within=NonNegativeReals, bounds=(b_tec.para_size_min, b_tec.para_size_max),
                                     units=u.MW)

        # CAPEX auxilliary (used to calculate theoretical CAPEX)
        # For new technologies, this is equal to actual CAPEX
        # For existing technologies it is used to calculate fixed OPEX
        b_tec.var_CAPEX_aux = Var(units=u.EUR)
        annualization_factor = mc.annualize(economics.discount_rate, economics.lifetime)
        if economics.capex_model == 1:
            b_tec.para_unit_CAPEX = Param(domain=Reals, initialize=economics.capex_data['unit_capex'],
                                          units=u.EUR/unit_size)
            b_tec.para_unit_CAPEX_annual = Param(domain=Reals,
                                                 initialize= annualization_factor * economics.capex_data['unit_capex'],
                                                 units=u.EUR/unit_size)
            b_tec.const_CAPEX_aux = Constraint(expr=b_tec.var_size * b_tec.para_unit_CAPEX_annual == b_tec.var_CAPEX_aux)
        elif economics.capex_model == 2:
            b_tec.para_bp_x = Param(domain=Reals, initialize=economics.capex_data['piecewise_capex']['bp_x'],
                                    units=unit_size)
            b_tec.para_bp_y = Param(domain=Reals, initialize=economics.capex_data['piecewise_capex']['bp_y'],
                                    units=u.EUR/unit_size)
            b_tec.para_bp_y_annual = Param(domain=Reals, initialize=annualization_factor *
                                                                    economics.capex_data['piecewise_capex']['bp_y'],
                                           units=u.EUR/unit_size)
            m_config.presolve.big_m_transformation_required = 1
            b_tec.const_CAPEX_aux = Piecewise(b_tec.var_CAPEX_aux, b_tec.var_size,
                                              pw_pts=b_tec.para_bp_x,
                                              pw_constr_type='EQ',
                                              f_rule=b_tec.para_bp_y,
                                              pw_repn='SOS2')

        # CAPEX
        if existing and not decommission:
            b_tec.var_CAPEX = Param(domain=Reals, initialize=0, units=u.EUR)
        else:
            b_tec.var_CAPEX = Var(units=u.EUR)
            if existing:
                b_tec.para_decommissioning_cost = Param(domain=Reals, initialize=economics.decommission_cost, units=u.EUR/unit_size)
                b_tec.const_CAPEX = Constraint(expr= b_tec.var_CAPEX == (b_tec.var_size_initial - b_tec.var_size) * b_tec.para_decommissioning_cost)
            else:
                b_tec.const_CAPEX = Constraint(expr= b_tec.var_CAPEX == b_tec.var_CAPEX_aux)

        # INPUT
        b_tec.set_input_carriers = Set(initialize=performance_data['input_carrier'])
        input_bounds = calculate_input_bounds(tec_data)
        if not technology_model == 'RES':
            def init_input_bounds(bounds, t, car):
                return input_bounds[car]
            b_tec.var_input = Var(model.set_t, b_tec.set_input_carriers, within=NonNegativeReals,
                                  bounds=init_input_bounds, units=u.MW)

        # OUTPUT
        b_tec.set_output_carriers = Set(initialize=performance_data['output_carrier'])
        output_bounds = calculate_output_bounds(tec_data)
        def init_output_bounds(bounds, t, car):
            return output_bounds[car]
        b_tec.var_output = Var(model.set_t, b_tec.set_output_carriers, within=NonNegativeReals,
                               bounds=init_output_bounds, units=u.MW)

        # VARIABLE OPEX
        b_tec.para_OPEX_variable = Param(domain=Reals, initialize=economics.opex_variable,
                                         units=u.EUR/u.MWh)
        b_tec.var_OPEX_variable = Var(model.set_t, units=u.EUR)
        def init_OPEX_variable(const, t):
            return sum(b_tec.var_output[t, car] for car in b_tec.set_output_carriers) * b_tec.para_OPEX_variable == \
                   b_tec.var_OPEX_variable[t]
        b_tec.const_OPEX_variable = Constraint(model.set_t, rule=init_OPEX_variable)

        # FIXED OPEX
        b_tec.para_OPEX_fixed = Param(domain=Reals, initialize=economics.opex_fixed,
                                      units=u.EUR/u.EUR)
        b_tec.var_OPEX_fixed = Var(units=u.EUR)
        b_tec.const_OPEX_fixed = Constraint(expr=b_tec.var_CAPEX_aux * b_tec.para_OPEX_fixed == b_tec.var_OPEX_fixed)


        # EMISSIONS
        b_tec.para_tec_emissionfactor = Param(domain=Reals, initialize=performance_data['emission_factor'],
                                              units=u.t/u.MWh)
        b_tec.var_tec_emissions_pos = Var(model.set_t, within=NonNegativeReals, units=u.t)
        b_tec.var_tec_emissions_neg = Var(model.set_t, within=NonNegativeReals, units=u.t)

        if technology_model == 'RES':
            # Set emissions to zero
            def init_tec_emissions_pos_RES(const, t):
                return b_tec.var_tec_emissions_pos[t] == 0
            b_tec.const_tec_emissions_pos = Constraint(model.set_t, rule=init_tec_emissions_pos_RES)
            def init_tec_emissions_neg_RES(const, t):
                return b_tec.var_tec_emissions_neg[t] == 0
            b_tec.const_tec_emissions_neg = Constraint(model.set_t, rule=init_tec_emissions_neg_RES)
        else:
            # Calculate emissions from emission factor
            def init_tec_emissions_pos(const, t):
                if performance_data['emission_factor'] >= 0:
                    return b_tec.var_input[t, performance_data['main_input_carrier']] \
                           * b_tec.para_tec_emissionfactor \
                           == b_tec.var_tec_emissions_pos[t]
                else:
                    return b_tec.var_tec_emissions_pos[t] == 0
            b_tec.const_tec_emissions = Constraint(model.set_t, rule=init_tec_emissions_pos)

            def init_tec_emissions_neg(const, t):
                if performance_data['emission_factor'] < 0:
                    return b_tec.var_input[t, performance_data['main_input_carrier']] \
                               (-b_tec.para_tec_emissionfactor) == \
                           b_tec.var_tec_emissions_neg[t]
                else:
                    return b_tec.var_tec_emissions_neg[t] == 0
            b_tec.const_tec_emissions_neg = Constraint(model.set_t, rule=init_tec_emissions_neg)


        # TECHNOLOGY PERFORMANCE
        if technology_model == 'RES': # Renewable technology with cap_factor as input
            b_tec = constraints_tec_RES(model, b_tec, tec_data)

        elif technology_model == 'CONV1': # n inputs -> n output, fuel and output substitution
            b_tec = constraints_tec_CONV1(model, b_tec, tec_data)

        elif technology_model == 'CONV2': # n inputs -> n output, fuel and output substitution
            b_tec = constraints_tec_CONV2(model, b_tec, tec_data)

        elif technology_model == 'CONV3':  # 1 input -> n outputs, output flexible, linear performance
            b_tec = constraints_tec_CONV3(model, b_tec, tec_data)

        elif technology_model == 'STOR': # Storage technology (1 input -> 1 output)
            if m_config.presolve.clustered_data == 1:
                hourly_order = data.k_means_specs.full_resolution['hourly_order']
            else:
                hourly_order = np.arange(1, len(model.set_t)+1)
            b_tec = constraints_tec_STOR(model, b_tec, tec_data, hourly_order)

        if m_config.presolve.big_m_transformation_required:
            mc.perform_disjunct_relaxation(b_tec)

        return b_tec

    # Create a new block containing all new technologies.
    if b_node.find_component('tech_blocks_new'):
        b_node.del_component(b_node.tech_blocks_new)
    b_node.tech_blocks_new = Block(set_tecsToAdd, rule=init_technology_block)

    # If it exists, carry over active tech blocks to temporary block
    if b_node.find_component('tech_blocks_active'):
        b_node.tech_blocks_existing = Block(b_node.set_tecsAtNode)
        for tec in b_node.set_tecsAtNode:
            b_node.tech_blocks_existing[tec].transfer_attributes_from(b_node.tech_blocks_active[tec])
        b_node.del_component(b_node.tech_blocks_active)

    # Create a block containing all active technologies at node
    if not set(set_tecsToAdd).issubset(b_node.set_tecsAtNode):
        b_node.set_tecsAtNode.add(set_tecsToAdd)

    def init_active_technology_blocks(bl, tec):
        if tec in set_tecsToAdd:
            bl.transfer_attributes_from(b_node.tech_blocks_new[tec])
        else:
            bl.transfer_attributes_from(b_node.tech_blocks_existing[tec])
    b_node.tech_blocks_active = Block(b_node.set_tecsAtNode, rule=init_active_technology_blocks)

    if b_node.find_component('tech_blocks_new'):
        b_node.del_component(b_node.tech_blocks_new)
    if b_node.find_component('tech_blocks_existing'):
        b_node.del_component(b_node.tech_blocks_existing)
    return b_node



def calculate_input_bounds(tec_data):
    """
    Calculates bounds for technology inputs for each input carrier
    """
    technology_model = tec_data.technology_model
    size_max = tec_data.size_max
    performance_data = tec_data.performance_data

    bounds = {}
    if technology_model == 'CONV3':
        main_car = performance_data['main_input_carrier']
        for c in performance_data['input_carrier']:
            if c == main_car:
                bounds[c] = (0, size_max)
            else:
                bounds[c] = (0, size_max * performance_data['input_ratios'][c])
    else:
        for c in performance_data['input_carrier']:
            bounds[c] = (0, size_max)
    return bounds

def calculate_output_bounds(tec_data):
    """
    Calculates bounds for technology outputs for each input carrier
    """
    technology_model = tec_data.technology_model
    size_is_int = tec_data.size_is_int
    size_max = tec_data.size_max
    performance_data = tec_data.performance_data
    fitted_performance = tec_data.fitted_performance
    if size_is_int:
        rated_power = fitted_performance['rated_power']
    else:
        rated_power = 1

    bounds = {}

    if technology_model == 'RES':  # Renewable technology with cap_factor as input
        cap_factor = fitted_performance['capacity_factor']
        for c in performance_data['output_carrier']:
            max_bound = float(size_max * max(cap_factor) * rated_power)
            bounds[c] = (0, max_bound)

    elif technology_model == 'CONV1':  # n inputs -> n output, fuel and output substitution
        performance_function_type = performance_data['performance_function_type']
        alpha1 = fitted_performance['out']['alpha1']
        for c in performance_data['output_carrier']:
            if performance_function_type == 1:
                max_bound = size_max * alpha1 * rated_power
            if performance_function_type == 2:
                alpha2 = fitted_performance['out']['alpha2']
                max_bound = size_max * (alpha1 + alpha2) * rated_power
            if performance_function_type == 3:
                alpha2 = fitted_performance['out']['alpha2']
                max_bound = size_max * (alpha1[-1] + alpha2[-1]) * rated_power
            bounds[c] = (0, max_bound)

    elif technology_model == 'CONV2':  # n inputs -> n output, fuel and output substitution
        alpha1 = {}
        alpha2 = {}
        performance_function_type = performance_data['performance_function_type']
        for c in performance_data['performance']['out']:
            alpha1[c] = fitted_performance[c]['alpha1']
            if performance_function_type == 1:
                max_bound = alpha1[c] * size_max * rated_power
            if performance_function_type == 2:
                alpha2[c] = fitted_performance[c]['alpha2']
                max_bound = size_max * (alpha1[c] + alpha2[c]) * rated_power
            if performance_function_type == 3:
                alpha2[c] = fitted_performance[c]['alpha2']
                max_bound = size_max * (alpha1[c][-1] + alpha2[c][-1]) * rated_power
            bounds[c] = (0, max_bound)

    elif technology_model == 'CONV3':  # 1 input -> n outputs, output flexible, linear performance
        alpha1 = {}
        alpha2 = {}
        performance_function_type = performance_data['performance_function_type']
        # Get performance parameters
        for c in performance_data['performance']['out']:
            alpha1[c] = fitted_performance[c]['alpha1']
            if performance_function_type == 1:
                max_bound = alpha1[c] * size_max * rated_power
            if performance_function_type == 2:
                alpha2[c] = fitted_performance[c]['alpha2']
                max_bound = size_max * (alpha1[c] + alpha2[c]) * rated_power
            if performance_function_type == 3:
                alpha2[c] = fitted_performance[c]['alpha2']
                max_bound = size_max * (alpha1[c][-1] + alpha2[c][-1]) * rated_power
            bounds[c] = (0, max_bound)

    elif technology_model == 'STOR':  # Storage technology (1 input -> 1 output)
        for c in performance_data['output_carrier']:
            bounds[c] = (0, size_max)

    return bounds