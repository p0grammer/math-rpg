"""
Mathpal — Procedural Equation Generator
========================================
Algorithmic math engine powered by SymPy that procedurally generates
randomized calculus problems across multiple topics and performs exact
symbolic verification of user responses.
"""

import random
import sympy as sp

x = sp.Symbol("x")


class MathProblem:
    """Represents a generated math problem with symbolic verification."""

    def __init__(self, expression_str, answer_str, sympy_target, topic="POWER_RULE",
                 operator_label="d/dx =", step_by_step=None, raw_data=None):
        self.expression_str = expression_str
        self.answer_str = answer_str
        self.sympy_target = sympy_target
        self.topic = topic
        self.operator_label = operator_label
        self.step_by_step = step_by_step or []
        self.raw_data = raw_data or {}

    def check_answer(self, user_input: str) -> bool:
        """
        Symbolic validation of student's answer.
        Accepts simplified forms, unsimplified sums, factored forms, and
        standard math notations (e.g. ^ or **).
        """
        if not user_input or not user_input.strip():
            return False

        # Clean string normalize
        clean_user = (
            user_input.strip()
            .replace(" ", "")
            .replace("*", "")
            .replace("X", "x")
            .replace("+C", "")
            .replace("+c", "")
        )
        clean_target = (
            self.answer_str.replace(" ", "")
            .replace("*", "")
            .replace("+C", "")
            .replace("+c", "")
        )

        if clean_user == clean_target:
            return True

        # Exact SymPy algebraic equivalence test
        try:
            # Format user string for SymPy parsing
            user_fmt = user_input.strip().replace("^", "**")
            # Strip integration constant + C if present
            if "+C" in user_fmt:
                user_fmt = user_fmt.replace("+C", "")
            elif "+c" in user_fmt:
                user_fmt = user_fmt.replace("+c", "")

            # Implicit multiplication helper: 4x -> 4*x, 4(x+1) -> 4*(x+1)
            parsed_user = sp.parse_expr(
                user_fmt,
                transformations=sp.parsing.sympy_parser.standard_transformations
                + (sp.parsing.sympy_parser.implicit_multiplication_application,),
            )
            diff = sp.simplify(parsed_user - self.sympy_target)
            return diff == 0
        except Exception:
            return False

    def __repr__(self):
        return f"<MathProblem '{self.expression_str}' -> '{self.answer_str}'>"


class EquationGenerator:
    """Generates procedural math problems for standard and boss campaign levels."""

    @classmethod
    def generate(cls, topic: str, difficulty: int = 1) -> MathProblem:
        """Dispatch to appropriate topic generator."""
        topic_upper = topic.upper()
        if topic_upper == "POWER_RULE":
            return cls.generate_power_rule(difficulty)
        elif topic_upper == "PRODUCT_RULE":
            return cls.generate_product_rule(difficulty)
        elif topic_upper == "QUOTIENT_RULE":
            return cls.generate_quotient_rule(difficulty)
        elif topic_upper == "CHAIN_RULE":
            return cls.generate_chain_rule(difficulty)
        elif topic_upper == "TRIG_DERIVATIVES":
            return cls.generate_trig_derivative(difficulty)
        elif topic_upper == "EXP_LOG_DERIVATIVES":
            return cls.generate_exp_log_derivative(difficulty)
        elif topic_upper == "BASIC_INTEGRALS":
            return cls.generate_basic_integral(difficulty)
        elif topic_upper == "U_SUBSTITUTION":
            return cls.generate_u_sub(difficulty)
        else:
            # Fallback to Power Rule
            return cls.generate_power_rule(difficulty)

    # ------------------------------------------------------------------
    # 1. Power Rule: c * x^n
    # ------------------------------------------------------------------
    @classmethod
    def generate_power_rule(cls, difficulty=1) -> MathProblem:
        c = random.randint(2, 4 + difficulty * 2)
        n = random.randint(2, 3 + difficulty)
        expr_str = f"{c}x^{n}" if n > 1 else f"{c}x"
        ans_c = c * n
        ans_n = n - 1
        if ans_n == 0:
            ans_str = f"{ans_c}"
        elif ans_n == 1:
            ans_str = f"{ans_c}x"
        else:
            ans_str = f"{ans_c}x^{ans_n}"

        target = ans_c * (x**ans_n)
        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="POWER_RULE",
            step_by_step=[
                f"Identify coefficient c={c} and exponent n={n}",
                f"Multiply c * n = {c} * {n} = {ans_c}",
                f"Subtract 1 from exponent: {n} - 1 = {ans_n}",
                f"Result: {ans_str}",
            ],
            raw_data={"c": c, "n": n, "ans_c": ans_c, "ans_n": ans_n},
        )

    # ------------------------------------------------------------------
    # 2. Product Rule: (ax^n)(bx^m)
    # ------------------------------------------------------------------
    @classmethod
    def generate_product_rule(cls, difficulty=1) -> MathProblem:
        a = random.randint(2, 3 + difficulty)
        n = random.randint(1, 2)
        b = random.randint(2, 4)
        m = 1

        u_str = f"{a}x^{n}" if n > 1 else f"{a}x"
        v_str = f"{b}x^{m}" if m > 1 else f"{b}x"
        expr_str = f"({u_str})({v_str})"

        # Derivative: u'v + uv'
        u_expr = a * x**n
        v_expr = b * x**m
        target = sp.diff(u_expr * v_expr, x)

        tot_c = a * b * (n + m)
        tot_exp = n + m - 1
        ans_str = f"{tot_c}x^{tot_exp}" if tot_exp > 1 else (f"{tot_c}x" if tot_exp == 1 else f"{tot_c}")

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="PRODUCT_RULE",
            step_by_step=[
                f"Set u = {u_str} and v = {v_str}",
                f"Compute u' = {sp.diff(u_expr, x)} and v' = {sp.diff(v_expr, x)}",
                f"Apply u'v + uv'",
                f"Simplify to: {ans_str}",
            ],
            raw_data={"u_coeff": a, "u_exp": n, "v_coeff": b, "v_exp": m},
        )

    # ------------------------------------------------------------------
    # 3. Quotient Rule: (u) / (v)
    # ------------------------------------------------------------------
    @classmethod
    def generate_quotient_rule(cls, difficulty=1) -> MathProblem:
        k = random.randint(2, 5)
        c = random.randint(1, 4)
        # Form: (kx) / (x + c)
        expr_str = f"({k}x)/(x+{c})"
        u_expr = k * x
        v_expr = x + c
        target = sp.diff(u_expr / v_expr, x)
        # derivative is k*c / (x+c)^2
        ans_num = k * c
        ans_str = f"{ans_num}/(x+{c})^2"

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="QUOTIENT_RULE",
            step_by_step=[
                f"u = {k}x, v = x + {c}",
                f"u' = {k}, v' = 1",
                f"Formula: (u'v - uv') / v^2",
                f"= ({k}(x+{c}) - {k}x(1)) / (x+{c})^2 = {ans_num}/(x+{c})^2",
            ],
            raw_data={"k": k, "c": c},
        )

    # ------------------------------------------------------------------
    # 4. Chain Rule: (ax + b)^n or sin(kx)
    # ------------------------------------------------------------------
    @classmethod
    def generate_chain_rule(cls, difficulty=1) -> MathProblem:
        a = random.randint(2, 4)
        b = random.randint(1, 5)
        n = random.randint(2, 4)

        expr_str = f"({a}x+{b})^{n}"
        inner = a * x + b
        target = sp.diff(inner**n, x)
        front_c = n * a
        exp_minus_1 = n - 1
        if exp_minus_1 == 1:
            ans_str = f"{front_c}({a}x+{b})"
        else:
            ans_str = f"{front_c}({a}x+{b})^{exp_minus_1}"

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="CHAIN_RULE",
            step_by_step=[
                f"Outer function: u^{n} -> {n}u^{exp_minus_1}",
                f"Inner function: u = {a}x + {b} -> u' = {a}",
                f"Multiply outer by inner: {n}({a}x+{b})^{exp_minus_1} * {a}",
                f"= {ans_str}",
            ],
            raw_data={"a": a, "b": b, "n": n, "front_c": front_c},
        )

    # ------------------------------------------------------------------
    # 5. Trig Derivatives: sin(kx), cos(kx)
    # ------------------------------------------------------------------
    @classmethod
    def generate_trig_derivative(cls, difficulty=1) -> MathProblem:
        k = random.randint(2, 6)
        func_type = random.choice(["sin", "cos"])

        if func_type == "sin":
            expr_str = f"sin({k}x)"
            target = sp.diff(sp.sin(k * x), x)
            ans_str = f"{k}cos({k}x)"
        else:
            expr_str = f"cos({k}x)"
            target = sp.diff(sp.cos(k * x), x)
            ans_str = f"-{k}sin({k}x)"

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="TRIG_DERIVATIVES",
            step_by_step=[
                f"d/dx( {func_type}(u) ) = { 'cos(u)' if func_type == 'sin' else '-sin(u)' } * u'",
                f"Here u = {k}x and u' = {k}",
                f"Result: {ans_str}",
            ],
            raw_data={"k": k, "type": func_type},
        )

    # ------------------------------------------------------------------
    # 6. Exponential & Log Derivatives: e^(kx), ln(x)
    # ------------------------------------------------------------------
    @classmethod
    def generate_exp_log_derivative(cls, difficulty=1) -> MathProblem:
        choice = random.choice(["exp", "log"])
        if choice == "exp":
            k = random.randint(2, 5)
            expr_str = f"e^({k}x)"
            target = sp.diff(sp.exp(k * x), x)
            ans_str = f"{k}e^({k}x)"
            steps = [f"d/dx( e^(kx) ) = k * e^(kx) with k={k}", f"Result: {ans_str}"]
        else:
            k = random.randint(2, 5)
            expr_str = f"{k}ln(x)"
            target = sp.diff(k * sp.log(x), x)
            ans_str = f"{k}/x"
            steps = [f"d/dx( ln(x) ) = 1/x", f"Result: {k} * (1/x) = {ans_str}"]

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="EXP_LOG_DERIVATIVES",
            step_by_step=steps,
        )

    # ------------------------------------------------------------------
    # 7. Basic Integrals: \int k x^n dx, \int sin(kx) dx
    # ------------------------------------------------------------------
    @classmethod
    def generate_basic_integral(cls, difficulty=1) -> MathProblem:
        # Generate antiderivative with clean integer coefficients
        n = random.randint(1, 3)
        new_n = n + 1
        mult = random.randint(1, 3)
        c = new_n * mult  # Ensures c / (n+1) is an integer!

        expr_str = f"\u222b {c}x^{n} dx" if n > 1 else (f"\u222b {c}x dx" if n == 1 else f"\u222b {c} dx")
        ans_c = mult
        ans_str = f"{ans_c}x^{new_n}" if new_n > 1 else f"{ans_c}x"
        target = ans_c * (x**new_n)

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="BASIC_INTEGRALS",
            operator_label="\u222b =",
            step_by_step=[
                f"Formula: \u222b c * x^n dx = c * x^(n+1) / (n+1)",
                f"Add 1 to exponent: {n} + 1 = {new_n}",
                f"Divide coefficient: {c} / {new_n} = {ans_c}",
                f"Antiderivative: {ans_str}",
            ],
            raw_data={"c": c, "n": n, "ans_c": ans_c, "new_n": new_n},
        )

    # ------------------------------------------------------------------
    # 8. U-Substitution: \int 2x (x^2 + 1)^n dx
    # ------------------------------------------------------------------
    @classmethod
    def generate_u_sub(cls, difficulty=1) -> MathProblem:
        n = random.randint(2, 4)
        expr_str = f"\u222b 2x(x^2+1)^{n} dx"
        # u = x^2 + 1, du = 2x dx -> \int u^n du = u^(n+1) / (n+1)
        new_n = n + 1
        ans_str = f"(x^2+1)^{new_n}/{new_n}"
        target = ((x**2 + 1)**new_n) / new_n

        return MathProblem(
            expression_str=expr_str,
            answer_str=ans_str,
            sympy_target=target,
            topic="U_SUBSTITUTION",
            operator_label="\u222b =",
            step_by_step=[
                "Set u = x^2 + 1, then du = 2x dx",
                f"Substitute: \u222b u^{n} du = u^{new_n} / {new_n}",
                f"Substitute back: (x^2+1)^{new_n} / {new_n}",
            ],
        )
