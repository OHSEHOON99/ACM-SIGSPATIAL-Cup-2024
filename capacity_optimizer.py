import logging

import cvxpy as cp
import numpy as np


def gaussian_decay(distances, bandwidth, capture_range):
    """
    Calculate Gaussian decay based on distance, bandwidth, and capture range.
    
    Args:
    - distances (np.ndarray): Distance matrix between demand points and candidate supply sites.
    - bandwidth (float): The bandwidth for the Gaussian decay function, controlling the spread of influence.
    - capture_range (float): Maximum range for coverage. Beyond this distance, the value is set to 0.

    In general, urban areas have a smaller service range compared to rural areas. 
    In this project, the Atlanta metropolitan region is modeled with a bandwidth of 1km and a capture range of 3km,
    while rural areas are modeled with a bandwidth of 3km and a capture range of 5km.
    
    Returns:
    - np.ndarray: Decay values based on Gaussian function.
    """
    decay_values = np.exp(-(distances ** 2) / (2 * bandwidth ** 2))
    decay_values[distances >= capture_range] = 0
    return decay_values


class CapacityOptimizer:
    """
    This class implements the Quadratic Programming (QP) model to optimize supply distribution for Electric Vehicle Charging Stations (EVCS)
    by minimizing the standard deviation of the Accessibility Index (Ai) at demand points using the 2SFCA (Two-Step Floating Catchment Area) method.

    Reference:
    Li, M., Wang, F., Kwan, M. P., Chen, J., & Wang, J. (2022). Equalizing the spatial accessibility of emergency medical services in Shanghai: 
    A trade-off perspective. Computers, Environment and Urban Systems, 92, 101745.
    """
    def __init__(self, total_supply, demand, distance_matrix, bandwidth, capture_range):
        """
        Initialize the CapacityOptimizer.

        Args:
        - total_supply (float): Total supply(= EV Ports) to be distributed among selected sites.
        - demand (np.ndarray): Demand values for each demand point.
        - distance_matrix (np.ndarray): Distance matrix between demand points and candidate supply sites.
        - bandwidth (float): Bandwidth for the Gaussian decay function.
        - capture_range (float): Maximum range for coverage.
        """
        self.total_supply = total_supply
        self.total_demand = np.sum(demand)
        self.A_bar_value = self.total_supply / self.total_demand  # Average supply per unit of demand
        self.F = gaussian_decay(distance_matrix, bandwidth, capture_range)
        self.D = np.diag(demand)
        self.capture_range = capture_range

    def optimize_capacity(self, current_sites, demand, constraints=(1, None)):
        """
        Optimize supply distribution across selected sites using Quadratic Programming (QP).

        Args:
        - current_sites (list): Indices of the currently selected sites.
        - demand (np.ndarray): Demand values for each demand point.
        - constraints (tuple): A tuple (x_min, x_max) specifying the lower and upper bounds for supply at each site.
        
        Returns:
        - optimized_supply (np.ndarray): Optimized supply values for the selected sites.
        - Ai_optimized (np.ndarray): Optimized Accessibility Index (Ai) values for the demand points.
        - A_hat (float): The root mean square deviation (RMSD) of the Ai values from the average accessibility.
        """
        try:
            F_current = self.F[:, current_sites]
            G_diag = 1.0 / np.sum(demand[:, np.newaxis] * F_current, axis=0)
            A_bar = np.full(F_current.shape[0], self.A_bar_value)
            P = F_current @ np.diag(G_diag)

            x = cp.Variable(len(current_sites))  # Variables representing the supply to be optimized at each site

            # Add a small epsilon to ensure numerical stability in the optimization.
            # The matrix P.T @ self.D @ P can potentially be near-singular,
            # meaning that its eigenvalues might be very close to zero, which can cause numerical issues
            # during optimization. Adding a small epsilon to the diagonal (as done here with np.eye) 
            # helps to make the matrix better conditioned (more stable for inversion or positive semi-definite operations).
            epsilon = 1e-8
            P_T_D_P = P.T @ self.D @ P + epsilon * np.eye(P.shape[1])

            # Use cp.psd_wrap to ensure that the matrix passed to cp.quad_form is treated as a 
            # positive semi-definite (PSD) matrix. In optimization problems, especially with quadratic forms, 
            # it's important for the matrix to be PSD to ensure the problem remains convex. 
            # By wrapping the matrix with cp.psd_wrap, we make sure cvxpy treats it correctly, even in cases 
            # where numerical precision might make it appear not PSD.
            objective = cp.Minimize(0.5 * cp.quad_form(x, cp.psd_wrap(P_T_D_P)) - (P.T @ self.D @ A_bar) @ x)

            # Define the constraints
            # In this project, for the Atlanta metropolitan area, the constraints are set to (2, 25),
            # meaning the minimum supply per site is 2, and the maximum is 25.
            # For other areas, the constraints are set to (1, None), meaning the minimum supply is 1
            # with no upper limit.
            constraint_list = []
            x_min, x_max = constraints
            
            # Add minimum and maximum constraints based on the area
            if x_min is not None:
                constraint_list.append(x >= x_min)
            if x_max is not None:
                constraint_list.append(x <= x_max)
            
            # Ensure the total supply matches the predefined total
            constraint_list.append(cp.sum(x) == self.total_supply)

            # Solve the QP problem
            prob = cp.Problem(objective, constraint_list)
            prob.solve(solver=cp.OSQP)

            optimized_supply = x.value
            Ai_optimized = P @ optimized_supply
            A_hat = self.calculate_metrics(Ai_optimized, demand, calculate_all=False)

        except Exception as e:
            logging.error(f"Optimization failed: {e}")
            optimized_supply = np.zeros(len(current_sites))
            Ai_optimized = np.full(len(demand), np.inf)
            A_hat = np.inf

        return optimized_supply, Ai_optimized, A_hat

    def calculate_metrics(self, Ai_optimized, demand, calculate_all=True):
        """
        Calculate various metrics for the optimized supply distribution.
        """
        diff = Ai_optimized - self.A_bar_value
        abs_diff = np.abs(diff)
        A_hat = np.sqrt(np.dot(diff ** 2, demand) / self.total_demand)

        if not calculate_all:
            return A_hat

        min_Ai = np.min(Ai_optimized)
        max_Ai = np.max(Ai_optimized)
        MD = np.max(abs_diff)
        MAD = np.dot(abs_diff, demand) / self.total_demand
        CV = A_hat / self.A_bar_value

        # Calculate Gini coefficient
        sorted_indices = np.argsort(Ai_optimized)
        sorted_Ai = Ai_optimized[sorted_indices]
        sorted_Di = demand[sorted_indices]
        
        sorted_Ai_Di = sorted_Ai * sorted_Di
        sum_Ai_Di = np.sum(sorted_Ai_Di)
        
        P = np.cumsum(sorted_Di) / self.total_demand
        T = np.cumsum(sorted_Ai_Di) / sum_Ai_Di
        Gini = 1 + np.sum(P[:-1] * T[1:]) - np.sum(T[:-1] * P[1:])

        return A_hat, min_Ai, max_Ai, MD, MAD, CV, Gini

    def calculate_coverage(self, selected_sites, distance_matrix, demand_values):
        """
        Calculate the coverage of demand within the capture range of the selected sites.
        """
        total_demand = np.sum(demand_values)

        if total_demand == 0:
            return 0

        distances_to_selected_sites = distance_matrix[:, selected_sites]
        covered_mask = np.any(distances_to_selected_sites <= self.capture_range, axis=1)
        covered_demand = np.sum(demand_values[covered_mask])
        coverage_ratio = (covered_demand / total_demand) * 100

        return coverage_ratio