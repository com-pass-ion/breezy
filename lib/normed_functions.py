"""
This module contains two Toolboxes *NormedFunctions* and *ModulateWith*,
containing functions for normalized wave forms.
Input is normed to [0, 1[ and Output to [0, 1].
"""

from math import sin, pi, exp
from functools import wraps

# Decorator
def validate_input(func):  # Empfängt ursprüngliche Funktion.
    @wraps(func)  # Übernimmt Namen und Docstring der Originalfunktion
    def wrapper(value, *args, **kwargs):  # Die Verpackung mit Platzhaltern für weitere Argumente.
        if not 0 <= value < 1:  # hinzugefügte Logik
            raise ValueError(f"Input out of Bound [0, 1[: {value} in {func.__name__}")
        return func(value, *args, **kwargs)  # Führt ursprüngliche Funktion aus.
    return wrapper  # Gibt Verpackung zurück.


class NormedFunction():
    """[0, 1[ -> [0, 1]:
    Input should exclude 1 to create repeatable pattern."""

    def __init__(self):  ## Instanzierungsschutz
        raise TypeError("Do not instantiate this Toolbox: NormedFunction")

    @staticmethod
    @validate_input
    def sine(x: float) -> float:
        """One full sine cycle mapped to [0, 1]."""
        # return 0.5 - 0.5 * cos(2 * pi * x)  # alternativ
        return 0.5 * sin(2*pi*x - pi/2) + 0.5

    @staticmethod
    @validate_input
    def saw_tooth(x: float) -> float:
        """Saw-tooth wave mapped to [0, 1]."""
        return x % 1

    @staticmethod
    @validate_input
    def reversed_saw_tooth(x:float) -> float:
        """Reversed saw-tooth mapped to [0, 1]."""
        return 1 - (x % 1)

    @staticmethod             
    @validate_input
    def triangle(x: float) -> float:
        """Triangular wave mapped to [0, 1]."""
        return 2 * abs(((x + 0.5) % 1.0) - 0.5)

    @staticmethod
    @validate_input
    def rectangle(x: float) -> float:
        """Squarewave mapped to [0, 1]."""
        return 0.0 if (x % 1) < 0.5 else 1.0

    @staticmethod
    @validate_input
    def gaussian(time: float, mu: float = 0.357142857, sigma: float = 0.18) -> float:
        """Applies normalized Gaussian function to *time* with given *mu* and *sigma*.
        time: Normalized time [0, 1].
        mu: The peak position (typically 0.5 for a symmetric pulse).
        sigma: The width of the pulse (recommended 0.1 to 0.2)."""
        return exp(-0.5 * ((time - mu) / sigma) ** 2)



class ModulateWith():
    """Goal: Flattening curves."""

    def __init__(self):
        raise TypeError("Do not instantiate this Toolbox: ModulateWith")

    @staticmethod
    @validate_input
    def inverse_cie1976(value: float) -> float:
        """Maps perceived brightness using the Inverse CIE 1976 Lightness function.
        """
        L_star = value * 100.0
        if L_star <= 8:
            return L_star / 903.3
        else:
            return ((L_star + 16) / 116) ** 3
        
    @staticmethod
    @validate_input
    def gamma_correction(value: float, gamma: float = 2.8) -> float:
        """Applies Gamma Correction with specified *gamma* to *value*.
        *gamma* < 1: Concave
        Small input values ​​are greatly expanded, large ones are compressed.
        *gamma* > 1: Convex
        Large input values ​​are greatly expanded, small ones are compressed."""
        return  value ** gamma
