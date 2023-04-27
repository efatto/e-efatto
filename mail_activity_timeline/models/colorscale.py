
def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    # >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    # >>> colorscale("#52D24F", 1.6)
    #83FF7E
    # >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    def clamp(val, minimum=0, maximum=255):
        if val < minimum:
            return minimum
        if val > maximum:
            return maximum
        return val

    hexstr = hexstr.strip('#')

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16),\
        int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)

    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))
