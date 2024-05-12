def convert_units(size: int):
    '''
    Converts size given in kB into more adequate units
    Arguments:
        size: int -> size to convert, given in kB
    Return:
        string consisting of number and unit
    '''
    CONVERSION_FACTOR = 1024
    UNITS = ['kB', 'MB', 'GB', 'TB', 'PB']
    x = size
    i_unit = 0
    while x/CONVERSION_FACTOR > CONVERSION_FACTOR and i_unit < len(UNITS):
        x = x/CONVERSION_FACTOR
        i_unit += 1
    return f'{x} {UNITS[i_unit]}'