"""
colors.base
===========
Convert colors between rgb, hsv, and hex, perform arithmetic, blend modes,
and generate random colors within boundaries.
"""
from __future__ import print_function
import colorsys
import random as random_

__all__ = ('Color', 'HSVColor', 'RGBColor', "RGBFloatColor", 'HexColor', 'ColorWheel',
           'rgb', 'hsv', 'hex', 'random')

HEX_RANGE = frozenset('0123456789abcdef')


def color_decorator(cls):
    attributes = cls.__dict__
    if 'Meta' in attributes and hasattr(attributes['Meta'], 'properties'):
        for index, prop in enumerate(attributes['Meta'].properties):
            # Assign pretty getters to each property name
            setattr(cls, prop, property(lambda self, index=index: self._color[index]))
    return cls


class Color(object):
    """ Abstract base class for all color types. """

    @property
    def hex(self):
        """ Hex is used the same way for all types. """
        return HexColor('{:02x}{:02x}{:02x}'.format(*[int(x) for x in self.rgb]))

    @property
    def rgb(self):
        raise NotImplementedError

    @property
    def hsv(self):
        raise NotImplementedError

    def multiply(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        return RGBColor(
            self_rgb.red * other_rgb.red / 255.0,
            self_rgb.green * other_rgb.green / 255.0,
            self_rgb.blue * other_rgb.blue / 255.0
        )

    __mul__ = multiply

    def add(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        return RGBColor(
            min(255, self_rgb.red + other_rgb.red),
            min(255, self_rgb.green + other_rgb.green),
            min(255, self_rgb.blue + other_rgb.blue),
        )

    __add__ = add

    def divide(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        if 0 in other_rgb:
            raise ZeroDivisionError
        return RGBColor(
            self_rgb.red / float(other_rgb.red),
            self_rgb.green / float(other_rgb.green),
            self_rgb.blue / float(other_rgb.blue),
        )

    __div__ = divide
    __truediv__ = divide

    def subtract(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        return RGBColor(
            max(0, (self_rgb.red - other_rgb.red)),
            max(0, (self_rgb.green - other_rgb.green)),
            max(0, (self_rgb.blue - other_rgb.blue)),
        )

    __sub__ = subtract

    def screen(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        return RGBColor(
            255 - (((255 - self_rgb.red) * (255 - other_rgb.red)) / 255.0),
            255 - (((255 - self_rgb.green) * (255 - other_rgb.green)) / 255.0),
            255 - (((255 - self_rgb.blue) * (255 - other_rgb.blue)) / 255.0),
        )

    def difference(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        return RGBColor(
            abs(self_rgb.red - other_rgb.red),
            abs(self_rgb.green - other_rgb.green),
            abs(self_rgb.blue - other_rgb.blue),
        )

    def overlay(self, other):
        return self.screen(self.multiply(other))

    def invert(self):
        return self.difference(RGBColor(255, 255, 255))

    def __eq__(self, other):
        self_rgb = self.rgb
        other_rgb = other.rgb
        return self_rgb.red == other_rgb.red \
           and self_rgb.green == other_rgb.green \
           and self_rgb.blue == other_rgb.blue

    def __contains__(self, item):
        return item in self._color

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        """ Treat the color object as an iterable to iterate over color values"""
        return iter(self._color)

    def __len__(self):
        return len(self._color)

    def __str__(self):
        return ', '.join(map(str, self._color))

    def __repr__(self):
        base = u'<{} {}>'
        properties = [
            '{}: {}'.format(prop, getattr(self, prop)) for prop in self.Meta.properties
        ]
        return base.format(self.__class__.__name__, ', '.join(properties))


@color_decorator
class HSVColor(Color):
    """ Hue Saturation Value """

    def __init__(self, h=0, s=0, v=0):
        if s > 1:
            raise ValueError('Saturation has to be less than 1')
        if v > 1:
            raise ValueError('Value has to be less than 1')

        # Hue can safely circle around 1
        if h >= 1:
            h -= int(h)

        self._color = h, s, v

    @property
    def rgb(self):
        return RGBColor(*map(lambda c: c * 255, colorsys.hsv_to_rgb(*self._color)))

    @property
    def hsv(self):
        return self

    @property
    def float(self):
        return RGBFloatColor(*map(lambda c: c, colorsys.hsv_to_rgb(*self._color)))

    class Meta:
        properties = ('hue', 'saturation', 'value')


@color_decorator
class RGBColor(Color):
    """ Red Green Blue """

    def __init__(self, r=0, g=0, b=0):
        self._color = round(r), round(g), round(b)
        for c in self._color:
            if 0 > c > 255:
                raise ValueError('Color values must be between 0 and 255')

    @property
    def rgb(self):
        return self

    @property
    def hsv(self):
        return HSVColor(*colorsys.rgb_to_hsv(*map(lambda c: c / 255.0, self._color)))

    @property
    def float(self):
        return RGBFloatColor(*map(lambda c: c / 255.0, self._color))

    class Meta:
        properties = ('red', 'green', 'blue')


@color_decorator
class RGBFloatColor(Color):
    """ Red Green Blue colors represented in a 0-1 values """
    def __init__(self, r=0, g=0, b=0):
        self._color = r, g, b
        for c in self._color:
            if 0 > c > 1:
                raise ValueError('Color values must be between 0 and 1')

    @property
    def hsv(self):
        return HSVColor(*colorsys.rgb_to_hsv(*map(lambda c: c, self._color)))

    @property
    def rgb(self):
        return self.hsv.rgb

    @property
    def float(self):
        return self

    class Meta:
        properties = ('red', 'green', 'blue')


class HexColor(RGBColor):
    """ Typical 6 digit hexadecimal colors.

    Warning: accuracy is lost when converting a color to hex
    """

    def __init__(self, hex='000000'):
        if len(hex) != 6:
            raise ValueError('Hex color must be 6 digits')

        hex = hex.lower()
        if not set(hex).issubset(HEX_RANGE):
            raise ValueError('Not a valid hex number')

        self._color = hex[:2], hex[2:4], hex[4:6]

    @property
    def rgb(self):
        return RGBColor(*[int(c, 16) for c in self._color])

    @property
    def hsv(self):
        return self.rgb.hsv

    @property
    def hex(self):
        return self

    @property
    def float(self):
        return RGBFloatColor(*[int(c, 16)/255.0 for c in self._color])

    def __str__(self):
        return '{}{}{}'.format(*self._color)


class ColorWheel(object):
    """ Iterate random colors distributed relatively evenly around the color wheel."""
    def __init__(self, start=0):
        # A 1.1 shift is identical to 0.1
        if start >= 1:
            start -= 1
        self._phase = start

    def __iter__(self):
        return self

    def __next__(self):
        shift = (random_.random() * 0.1) + 0.1
        self._phase += shift
        if self._phase >= 1:
            self._phase -= 1
        return HSVColor(self._phase, 1, 0.8)

    next = __next__  # for Python 2


def random():  # This name might be a bad idea?
    """ Generate a random color."""
    return HSVColor(random_.random(), random_.random(), random_.random())


# Simple aliases
rgb = RGBColor  # rgb(100, 100, 100), or rgb(r=100, g=100, b=100)
hsv = HSVColor  # hsv(0.5, 1, 1), or hsv(h=0.5, s=1, v=1)
hex = HexColor  # hex('bada55')
