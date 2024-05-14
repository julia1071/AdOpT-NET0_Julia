from pyomo.environ import *
from pyomo.gdp import *
import copy
from warnings import warn
import numpy as np

from src.components.technologies.utilities import FittedPerformance
from src.components.technologies.technology import Technology


class CO2storageDetailed(Technology):
    """
    This model resembles a permanent storage technology (sink). It takes energy and a main carrier (e.g. CO2, H2 etc)
    as inputs, and it has no output.


    **Variable declarations:**

    - Storage level in :math:`t`: :math:`E_t`

    **Constraint declarations:**

    - Maximal injection rate:

      .. math::
        Input_{t} \leq Inj_rate

    - Size constraint:

      .. math::
        E_{t} \leq Size

    - Storage level calculation:

      .. math::
        E_{t} = E_{t-1} + Input_{t}

    - If an energy consumption for the injection is given, the respective carrier input is:

      .. math::
        Input_{t, car} = cons_{car, in} Input_{t}

    """

    def __init__(self, tec_data):
        super().__init__(tec_data)

        self.fitted_performance = FittedPerformance()

    def fit_technology_performance(self, climate_data, location):
        """
        Fits conversion technology type SINK and returns fitted parameters as a dict

        :param node_data: contains data on demand, climate data, etc.
        """

        time_steps = len(climate_data)

        # Main carrier (carrier to be stored)
        self.main_car = self.performance_data["main_input_carrier"]

        # Input Bounds
        for car in self.performance_data["input_carrier"]:
            if car == self.performance_data["main_input_carrier"]:
                self.fitted_performance.bounds["input"][car] = np.column_stack(
                    (np.zeros(shape=(time_steps)), np.ones(shape=(time_steps)))
                )
            else:
                if "energy_consumption" in self.performance_data["performance"]:
                    energy_consumption = self.performance_data["performance"][
                        "energy_consumption"
                    ]
                    self.fitted_performance.bounds["input"][car] = np.column_stack(
                        (
                            np.zeros(shape=(time_steps)),
                            np.ones(shape=(time_steps)) * energy_consumption["in"][car],
                        )
                    )

        # Time dependent coefficents
        self.fitted_performance.time_dependent_coefficients = 0

    def construct_tech_model(self, b_tec, energyhub):
        """
        Adds constraints to technology blocks for tec_type SINK, resembling a permanent storage technology

        :param b_tec:
        :param energyhub:
        :return: b_tec
        """

        super(Sink, self).construct_tech_model(b_tec, energyhub)

        set_t_full = energyhub.model.set_t_full

        # DATA OF TECHNOLOGY
        performance_data = self.performance_data
        coeff = self.fitted_performance.coefficients


        # Additional decision variables
        b_tec.var_storage_level = Var(
            set_t_full,
            domain=NonNegativeReals,
            bounds=(b_tec.para_size_min, b_tec.para_size_max),
        )

        # Size constraint
        def init_size_constraint(const, t):
            return b_tec.var_storage_level[t] <= b_tec.var_size

        b_tec.const_size = Constraint(set_t_full, rule=init_size_constraint)

        # Constraint storage level
        if (
            energyhub.model_information.clustered_data
            and not self.modelled_with_full_res
        ):

            def init_storage_level(const, t):
                if t == 1:
                    return (
                        b_tec.var_storage_level[t]
                        == self.input[self.sequence[t - 1], self.main_car]
                    )
                else:
                    return (
                        b_tec.var_storage_level[t]
                        == b_tec.var_storage_level[t - 1]
                        + self.input[self.sequence[t - 1], self.main_car]
                    )

        else:

            def init_storage_level(const, t):
                if t == 1:
                    return b_tec.var_storage_level[t] == self.input[t, self.main_car]
                else:
                    return (
                        b_tec.var_storage_level[t]
                        == b_tec.var_storage_level[t - 1] + self.input[t, self.main_car]
                    )

            b_tec.const_storage_level = Constraint(set_t_full, rule=init_storage_level)

        # Maximal injection rate
        def init_maximal_injection(const, t):
            return (
                self.input[t, self.main_car]
                <= self.performance_data["injection_rate_max"]
            )

        b_tec.const_max_charge = Constraint(self.set_t, rule=init_maximal_injection)

        # Electricity consumption for compression
        # Additional sets
        b_tec.var_bhp = Var(self.set_t, within=NonNegativeReals)
        # TODO add constraint on relationship bhp and wellhead pressure
        b_tec.var_pwellhead = Var(self.set_t, within=NonNegativeReals)
        b_tec.var_pratio = Var(self.set_t, within=NonNegativeReals)

        b_tec.const_pratio = Constraint(self.set_t, rule=b_tec.var_pratio == 5)


        nr_segments =2
        b_tec.set_pieces = RangeSet(1, nr_segments)
        eta = [0.2, 0.8]
        pratio_range = [0, 10, 20]

        def init_input_output(dis, t, ind):
            # Input-output (eq. 2)
            def init_output(const):
                return (
                    self.output[t, "electricity"]
                    == eta[t - 1, ind - 1] * self.input[t, self.main_car]
                )

            dis.const_output = Constraint(rule=init_output)

            # Lower bound on the energy input (eq. 5)
            def init_input_low_bound(const):
                return (
                    pratio_range[t - 1, ind - 1]
                    <= b_tec.var_pratio[t]
                )

            dis.const_input_on1 = Constraint(rule=init_input_low_bound)

            # Upper bound on the energy input (eq. 5)
            def init_input_up_bound(const):
                return (
                    b_tec.var_pratio[t]
                    <= pratio_range[t - 1, ind]
                )

            dis.const_input_on2 = Constraint(rule=init_input_up_bound)

        b_tec.dis_input_output = Disjunct(
            self.set_t, b_tec.set_pieces, rule=init_input_output
        )

        # Bind disjuncts
        def bind_disjunctions(dis, t):
            return [b_tec.dis_input_output[t, i] for i in b_tec.set_pieces]

        b_tec.disjunction_input_output = Disjunction(self.set_t, rule=bind_disjunctions)

        return b_tec

