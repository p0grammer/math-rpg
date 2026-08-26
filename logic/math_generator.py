"""
Mathpal — Math Problem Generators
==================================
Generates Power Rule and Product Rule differentiation problems with
symbolic validation and step-by-step breakdown data.
"""

import random
import sympy as sp


class PowerRuleProblem:
    """
    A single Power Rule problem: f(x) = c * x^n.
    """

    def __init__(self, coefficient, variable, exponent):
        self.coefficient = coefficient
        self.variable = variable
        self.exponent = exponent

    @property
    def expression_str(self):
        parts = []
        if self.coefficient == -1:
            parts.append("-")
        elif self.coefficient != 1:
            parts.append(str(self.coefficient))
        parts.append(self.variable)
        if self.exponent != 1:
            parts.append(f"^{self.exponent}")
        return "".join(parts)

    @property
    def answer_coefficient(self):
        return self.coefficient * self.exponent

    @property
    def answer_exponent(self):
        return self.exponent - 1

    @property
    def answer_str(self):
        nc = self.answer_coefficient
        ne = self.answer_exponent
        if ne == 0:
            return str(nc)
        parts = []
        if nc == -1:
            parts.append("-")
        elif nc != 1:
            parts.append(str(nc))
        parts.append(self.variable)
        if ne != 1:
            parts.append(f"^{ne}")
        return "".join(parts)

    def check_answer(self, user_input):
        """Robust answer validation supporting standard and algebraic forms."""
        user_clean = user_input.strip().replace(" ", "").replace("*", "").replace("X", "x")
        ans_clean = self.answer_str.replace(" ", "").replace("*", "")
        if user_clean == ans_clean:
            return True

        # SymPy algebraic equality fallback
        try:
            x = sp.Symbol("x")
            user_expr = sp.sympify(user_input.replace("^", "**"))
            target_expr = sp.sympify(self.answer_str.replace("^", "**"))
            return sp.simplify(user_expr - target_expr) == 0
        except Exception:
            return False


class ProductRuleProblem:
    """
    A single Product Rule problem: f(x) = (a * x^n) * (b * x^m).
    
    Formula:
        d/dx[ u * v ] = u' * v + u * v'
    """

    def __init__(self, u_coeff, u_exp, v_coeff, v_exp, variable="x"):
        self.u_coeff = u_coeff
        self.u_exp = u_exp
        self.v_coeff = v_coeff
        self.v_exp = v_exp
        self.variable = variable

    def _format_factor(self, c, exp):
        parts = []
        if c == -1:
            parts.append("-")
        elif c != 1:
            parts.append(str(c))
        parts.append(self.variable)
        if exp != 1:
            parts.append(f"^{exp}")
        return "".join(parts)

    @property
    def u_str(self):
        return self._format_factor(self.u_coeff, self.u_exp)

    @property
    def v_str(self):
        return self._format_factor(self.v_coeff, self.v_exp)

    @property
    def expression_str(self):
        """Formatted as e.g. '(2x^2)(3x)'."""
        return f"({self.u_str})({self.v_str})"

    # Derivatives of each factor
    @property
    def du_coeff(self):
        return self.u_coeff * self.u_exp

    @property
    def du_exp(self):
        return self.u_exp - 1

    @property
    def du_str(self):
        if self.du_exp == 0:
            return str(self.du_coeff)
        return self._format_factor(self.du_coeff, self.du_exp)

    @property
    def dv_coeff(self):
        return self.v_coeff * self.v_exp

    @property
    def dv_exp(self):
        return self.v_exp - 1

    @property
    def dv_str(self):
        if self.dv_exp == 0:
            return str(self.dv_coeff)
        return self._format_factor(self.dv_coeff, self.dv_exp)

    # First term: u' * v
    @property
    def term1_coeff(self):
        return self.du_coeff * self.v_coeff

    @property
    def term1_exp(self):
        return self.du_exp + self.v_exp

    @property
    def term1_str(self):
        if self.term1_exp == 0:
            return str(self.term1_coeff)
        return self._format_factor(self.term1_coeff, self.term1_exp)

    # Second term: u * v'
    @property
    def term2_coeff(self):
        return self.u_coeff * self.dv_coeff

    @property
    def term2_exp(self):
        return self.u_exp + self.dv_exp

    @property
    def term2_str(self):
        if self.term2_exp == 0:
            return str(self.term2_coeff)
        return self._format_factor(self.term2_coeff, self.term2_exp)

    # Simplified final sum
    @property
    def answer_coeff(self):
        return self.term1_coeff + self.term2_coeff

    @property
    def answer_exp(self):
        return self.term1_exp  # Since term1_exp == term2_exp for monomial products

    @property
    def answer_str(self):
        """The canonical simplified derivative string, e.g. '18x^2'."""
        if self.answer_exp == 0:
            return str(self.answer_coeff)
        return self._format_factor(self.answer_coeff, self.answer_exp)

    def check_answer(self, user_input):
        """Validate answer accepting simplified or product-rule expanded forms."""
        user_clean = user_input.strip().replace(" ", "").replace("*", "").replace("X", "x")
        ans_clean = self.answer_str.replace(" ", "").replace("*", "")
        if user_clean == ans_clean:
            return True

        # Check expanded sum form: term1 + term2 or term2 + term1
        t1 = self.term1_str.replace(" ", "").replace("*", "")
        t2 = self.term2_str.replace(" ", "").replace("*", "")
        if user_clean in (f"{t1}+{t2}", f"{t2}+{t1}"):
            return True

        # SymPy exact algebraic validation
        try:
            x = sp.Symbol("x")
            u_expr = self.u_coeff * x**self.u_exp
            v_expr = self.v_coeff * x**self.v_exp
            actual_deriv = sp.diff(u_expr * v_expr, x)
            user_expr = sp.sympify(user_input.replace("^", "**"))
            return sp.simplify(user_expr - actual_deriv) == 0
        except Exception:
            return False


class MathGenerator:
    """Problem generator factory."""

    @staticmethod
    def generate_power_rule(difficulty=1):
        if difficulty <= 1:
            coeff = random.randint(2, 6)
            exp = random.randint(2, 4)
        elif difficulty <= 2:
            coeff = random.randint(2, 10)
            exp = random.randint(2, 6)
        else:
            coeff = random.choice([c for c in range(-10, 11) if c != 0])
            exp = random.randint(2, 8)
        return PowerRuleProblem(coeff, "x", exp)

    @staticmethod
    def generate_product_rule(difficulty=1):
        """
        Generate (u)(v) product rule problems.
        Example: (2x^2)(3x) -> 18x^2
        """
        if difficulty <= 1:
            u_c = random.randint(2, 4)
            u_e = random.randint(1, 2)
            v_c = random.randint(2, 4)
            v_e = 1
        elif difficulty <= 2:
            u_c = random.randint(2, 5)
            u_e = random.randint(1, 3)
            v_c = random.randint(2, 5)
            v_e = random.randint(1, 2)
        else:
            u_c = random.randint(2, 7)
            u_e = random.randint(1, 4)
            v_c = random.randint(2, 7)
            v_e = random.randint(1, 3)
        return ProductRuleProblem(u_c, u_e, v_c, v_e, "x")
