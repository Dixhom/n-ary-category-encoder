import math
import json
import pyqrcode
import re
from collections import OrderedDict
from sys import getsizeof


class JsonFile:
    """save a json file"""

    def __init__(self, path):
        """
        Args:
            path (str): path to save the json file
        """
        self.path = path

    def load(self):
        """load data from a json file

        Returns:
            dict or list: loaded data
        """
        with open(self.path, 'r') as f:
            return json.load(f)

    def dump(self, data):
        """dump data to a json file

        Args:
            data (str): data to be dumped
        """
        with open(self.path, 'w') as f:
            json.dump(data, f)


class NaryEncoder:
    """Encode data using N-ary system
    """

    def __init__(self, json_path):
        """init

        Args:
            json_path (str): json path to save a config file
        """
        self.json_path = json_path
        # length of the data (list)
        self.ln = 0
        # max element of the data (list)
        self.mx = 0

    def encode(self, l, l_master):
        """encode data to an n-ary number

        Args:
            l (list): chosen values for each category
            l_master (OrderedDictionary): entire list of values for each category

        Raises:
            ValueError: encoded value is overflown

        Returns:
            _type_: encoded n-ary value
        """
        self.ln = len(l)
        self.mx = max(l_master)
        j = JsonFile(self.json_path)
        j.dump([self.ln, self.mx])

        # logarray = [math.log2(self.mx) * i + math.log2(x)
        #             for i, x in enumerate(l_master)]
        # is_overflow = any([x > 64 for x in logarray])
        # if is_overflow:
        #     raise ValueError('overflow')

        enc = [self.mx ** i * x for i, x in enumerate(l)]
        enc = sum(enc)
        return int(enc)

    def decode(self, enc):
        """decode an n-ary value

        Args:
            enc (int): encoded n-ary value

        Returns:
            _type_: decoded list of chosen categories
        """
        if self.ln == 0 and self.mx == 0:
            j = JsonFile(self.json_path)
            self.ln, self.mx = j.load()

        dec = []
        remainder = enc
        for i in range(self.ln - 1, -1, -1):
            div = self.mx ** i
            dec.append(int(remainder // div))
            remainder %= div
        dec = dec[::-1]
        return dec


def create_qr_code(value=None,
                   error='L',
                   version=1,
                   mode='binary',
                   path=None,
                   scale=5,
                   module_color=[0, 0, 0, 128],
                   background=[255, 255, 255],
                   adjust=True,
                   max_iteration=10):
    """create a QR code

    Args:
        value (data, optional): value to be encoded into a QR code. Defaults to None.
        error (str, optional): error correction type. Defaults to 'L'.
        version (int, optional): size of the QR code. Defaults to 1.
        mode (str, optional): type of value. Defaults to 'binary'.
        path (_type_, optional): path to . Defaults to None.
        scale (int, optional): _description_. Defaults to 5.
        module_color (list, optional): color of the QR code dots. Defaults to [0, 0, 0, 128].
        background (list, optional): color of the QR code background. Defaults to [255, 255, 255].
        adjust (bool, optional): whether automatically adjust version and mode. Defaults to True.
        max_iteration (int, optional): max iteration for the adjusting loop. Defaults to 10.

    Raises:
        ValueError: max iteration exceeded
        ex: exception raised when creating a QR code
    """

    itercnt = 0
    while True:
        # avoid infinite loops
        itercnt += 1
        if itercnt >= max_iteration:
            raise ValueError('max iteration exceeded')

        try:
            # encode to a qr code
            code = pyqrcode.create(
                value, error=error, version=version, mode=mode)
        except Exception as ex:
            # if mode and version are not auto-adjusted, end here
            if not adjust:
                raise ex
            # check the right mode
            m = re.match(
                f'The content provided cannot be encoded with the mode {mode}, it can only be encoded as ([a-z]+)\.', str(ex))
            if m:
                mode = m.group(1)
                continue
            # check the right version
            m = re.match(
                f'The data will not fit inside a version {version} code with the given encoding and error level \(the code must be at least a version (\d+)\)\.', str(ex))
            if m:
                version = int(m.group(1))
                continue
            # if an unknown error occurred, stop.
            raise ex
        else:
            code.png(path, scale=scale, module_color=module_color,
                     background=background)
            break


class CategoricalEncoder:
    """encode categories to numbers"""

    def __init__(self, category_dict):
        """init

        Args:
            category_dict (OrderedDict): dictionary of categorical information
        """
        self.category_dict = category_dict

    def encode(self, category_list):
        """encode categories to numbers

        Args:
            category_list (list): list of chosen categories

        Returns:
            _type_: encoded categories
        """
        lst = [v.index(l) for l, v in zip(
            category_list, self.category_dict.values())]
        lst_master = [len(v) for v in self.category_dict.values()]
        return lst, lst_master

    def decode(self, category_indices):
        """decode numbers to categories

        Args:
            category_indices (list): indices for categories

        Returns:
            _type_: decoded categories
        """
        return [v[i] for i, v in zip(category_indices, self.category_dict.values())]


if __name__ == '__main__':
    # --- here is an example

    # test data
    carinfo = OrderedDict()
    carinfo['manufacturer'] = ['VW', 'Toyota',
                               'Renault', 'GM', 'Hyundai', 'Ford', 'Honda']
    carinfo['body_style'] = ['coupe', 'hatchback',
                             'wagon', 'sedan', 'convertible' 'suv']
    carinfo['trim_level'] = ['standard', 'sport', 'luxury']
    carinfo['assembly_plant'] = ['0', '1', '2', '3',
                                 '4', '5', '6', '7', '8', '9', '10', '11']
    print('test data: ', carinfo)

    # chosen elements from categories
    categories = ['Toyota', 'coupe', 'standard', '8']
    print('chosen elements from categories: ', categories)

    # initialize
    ce = CategoricalEncoder(carinfo)
    # encode
    indices, master = ce.encode(['Toyota', 'coupe', 'standard', '8'])
    print('indices', indices, 'master', master)

    # encoded
    ne = NaryEncoder('params.json')
    enc = ne.encode(indices, master)
    print('encoded', enc)

    # decode
    ne = NaryEncoder('params.json')
    dec = ne.decode(enc)
    print('decoded', dec)

    print('are decoded data same as the raw one?', dec == indices)

    # decode
    restored = ce.decode(dec)
    print('restored', restored)

    print('are restored data same as the raw one?', restored == categories)

    print('size of raw data [bytes]', getsizeof(str(categories)))
    print('size of encoded data [bytes]', getsizeof(enc))

    # --- QR code generation

    # raw_data
    raw_data = str(categories)
    path = 'raw_data.png'
    create_qr_code(value=raw_data,
                   error='L',
                   version=1,
                   mode='binary',
                   path=path)

    # encoded_data
    path = 'enc_data.png'
    create_qr_code(value=enc,
                   error='L',
                   version=1,
                   mode='numeric',
                   path=path)
