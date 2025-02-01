from __future__ import unicode_literals
import frappe
# import jinja2
#from num2words import num2words
from frappe.utils import flt, cint
import re
from decimal import Decimal
from math import floor



@frappe.whitelist()
def getTotalInWordsAr(num):
    # return num2words(num,to='currency',lang='ar')
    return money_in_words(num, lang='ar')


@frappe.whitelist()
def getTotalInWordsEn(num):
    return num2words(num, to='currency')

@frappe.whitelist()
def formatDate(date):
    return frappe.format(date)


def money_in_words(number, main_currency=None, fraction_currency=None, lang="", show_currency=True, omit_only=False):
    if lang == "":
        lang = frappe.local.lang
    """
    Returns string in words with currency and fraction currency.
    """

    from frappe.utils import get_defaults
    _ = frappe._

    try:
        # note: `flt` returns 0 for invalid input and we don't want that
        number = float(number)
    except ValueError:
        return ""

    number = flt(number)
    if number < 0:
        return ""

    d = get_defaults()
    if not main_currency:
        main_currency = d.get('currency', 'SAR')
    if not fraction_currency:
        fraction_currency = frappe.db.get_value("Currency", main_currency, "fraction", cache=True) or _("Cent")
        fraction_currency = (_(fraction_currency, lang) if lang != None else fraction_currency)
    number_format = frappe.db.get_value("Currency", main_currency, "number_format", cache=True) or \
                    frappe.db.get_default("number_format") or "#,###.##"

    fraction_length = get_number_format_info(number_format)[2]

    n = "%.{0}f".format(fraction_length) % number

    numbers = n.split('.')
    main, fraction = numbers if len(numbers) > 1 else [n, '00']

    if len(fraction) < fraction_length:
        zeros = '0' * (fraction_length - len(fraction))
        fraction += zeros

    in_million = True
    if number_format == "#,##,###.##": in_million = False

    # 0.00
    if main == '0' and fraction in ['00', '000']:
        out = "{0} {1}".format(main_currency, _('Zero'))
    # 0.XX
    elif main == '0':
        out = _(in_words(fraction, in_million, lang).title()) + ' ' + fraction_currency
    else:
        out = _(in_words(main, in_million, lang).title()) + '  ' + (
            _(main_currency, lang) if show_currency else '')  # (_(main_currency,lang) if show_currency else '') + ' ' +
        if cint(fraction):
            out = out + ' ' + _('and', lang) + ' ' + _(
                in_words(fraction, in_million, lang).title()) + ' ' + _(fraction_currency)

    return (_('فقط', lang) if omit_only == False else '') + ' ' + out.replace('،', ' , ').replace(',', _("and",lang=lang)).replace('SAR', _("ريال سعودى")).replace('EGP', _("جنيه مصري")).replace('Halala', _("هلله")).replace('Piastre[F]', _("قرش"))


# convert number to words
#
def in_words(integer, in_million=True, lang=""):
    """
    Returns string in words for the given integer.
    """
    # frappe.msgprint(lang)
    # locale = 'en_IN' if not in_million else frappe.local.lang
    locale = (lang if lang != "" else ('en_IN' if not in_million else frappe.local.lang))
    integer = int(integer)
    try:
        ret = num2words(integer, lang=locale)
    except NotImplementedError:
        ret = num2words(integer, lang='en')
    except OverflowError:
        ret = num2words(integer, lang='en')
    return ret.replace('-', ' ')


number_format_info = {
    "#,###.##": (".", ",", 2),
    "#.###,##": (",", ".", 2),
    "# ###.##": (".", " ", 2),
    "# ###,##": (",", " ", 2),
    "#'###.##": (".", "'", 2),
    "#, ###.##": (".", ", ", 2),
    "#,##,###.##": (".", ",", 2),
    "#,###.###": (".", ",", 3),
    "#.###": ("", ".", 0),
    "#,###": ("", ",", 0)
}


def get_number_format_info(format):
    return number_format_info.get(format) or (".", ",", 2)

CONVERTES_TYPES = ['cardinal', 'ordinal', 'ordinal_num', 'year', 'currency']

def num2words(number, ordinal=False, lang='en', to='cardinal', **kwargs):

    converter = Num2Word_AR()

    if isinstance(number, str):
        number = converter.str_to_number(number)

    # backwards compatible
    if ordinal:
        return converter.to_ordinal(number)

    if to not in CONVERTES_TYPES:
        raise NotImplementedError()

    return getattr(converter, 'to_{}'.format(to))(number, **kwargs)




CURRENCY_SR = [("ريال", "ريالان", "ريالات", "ريالاً"),
               ("هللة", "هللتان", "هللات", "هللة")]
CURRENCY_EGP = [("جنيه", "جنيهان", "جنيهات", "جنيهاً"),
                ("قرش", "قرشان", "قروش", "قرش")]
CURRENCY_KWD = [("دينار", "ديناران", "دينارات", "ديناراً"),
                ("فلس", "فلسان", "فلس", "فلس")]

ARABIC_ONES = [
    "", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية",
    "تسعة",
    "عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر",
    "ستة عشر", "سبعة عشر", "ثمانية عشر",
    "تسعة عشر"
]


class Num2Word_AR(object):
    errmsg_too_big = "Too large"
    max_num = 10 ** 36

    def __init__(self):
        self.number = 0
        self.arabicPrefixText = ""
        self.arabicSuffixText = ""
        self.integer_value = 0
        self._decimalValue = ""
        self.partPrecision = 2
        self.currency_unit = CURRENCY_SR[0]
        self.currency_subunit = CURRENCY_SR[1]
        self.isCurrencyPartNameFeminine = True
        self.isCurrencyNameFeminine = False
        self.separator = 'و'

        self.arabicOnes = ARABIC_ONES
        self.arabicFeminineOnes = [
            "", "إحدى", "اثنتان", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثمان",
            "تسع",
            "عشر", "إحدى عشرة", "اثنتا عشرة", "ثلاث عشرة", "أربع عشرة",
            "خمس عشرة", "ست عشرة", "سبع عشرة", "ثماني عشرة",
            "تسع عشرة"
        ]
        self.arabicOrdinal = [
            "", "اول", "ثاني", "ثالث", "رابع", "خامس", "سادس", "سابع", "ثامن",
            "تاسع", "عاشر", "حادي عشر", "ثاني عشر", "ثالث عشر", "رابع عشر",
            "خامس عشر", "سادس عشر", "سابع عشر", "ثامن عشر", "تاسع عشر"
        ]
        self.arabicTens = [
            "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون",
            "تسعون"
        ]
        self.arabicHundreds = [
            "", "مائة", "مئتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة",
            "سبعمائة", "ثمانمائة", "تسعمائة"
        ]
        self.arabicAppendedTwos = [
            "مئتا", "ألفا", "مليونا", "مليارا", "تريليونا", "كوادريليونا",
            "كوينتليونا", "سكستيليونا"
        ]
        self.arabicTwos = [
            "مئتان", "ألفان", "مليونان", "ملياران", "تريليونان",
            "كوادريليونان", "كوينتليونان", "سكستيليونان"
        ]
        self.arabicGroup = [
            "مائة", "ألف", "مليون", "مليار", "تريليون", "كوادريليون",
            "كوينتليون", "سكستيليون"
        ]
        self.arabicAppendedGroup = [
            "", "ألفاً", "مليوناً", "ملياراً", "تريليوناً", "كوادريليوناً",
            "كوينتليوناً", "سكستيليوناً"
        ]
        self.arabicPluralGroups = [
            "", "آلاف", "ملايين", "مليارات", "تريليونات", "كوادريليونات",
            "كوينتليونات", "سكستيليونات"
        ]

    def number_to_arabic(self, arabic_prefix_text, arabic_suffix_text):
        self.arabicPrefixText = arabic_prefix_text
        self.arabicSuffixText = arabic_suffix_text
        self.extract_integer_and_decimal_parts()

    def extract_integer_and_decimal_parts(self):
        re.split('\\.', str(self.number))
        splits = re.split('\\.', str(self.number))

        self.integer_value = int(splits[0])
        if len(splits) > 1:
            self._decimalValue = int(self.decimal_value(splits[1]))
        else:
            self._decimalValue = 0

    def decimal_value(self, decimal_part):

        if self.partPrecision is not len(decimal_part):
            decimal_part_length = len(decimal_part)

            decimal_part_builder = decimal_part
            for i in range(0, self.partPrecision - decimal_part_length):
                decimal_part_builder += '0'
            decimal_part = decimal_part_builder

            if len(decimal_part) <= self.partPrecision:
                dec = len(decimal_part)
            else:
                dec = self.partPrecision
            result = decimal_part[0: dec]
        else:
            result = decimal_part

        for i in range(len(result), self.partPrecision):
            result += '0'
        return result

    def digit_feminine_status(self, digit, group_level):
        if group_level == -1:
            if self.isCurrencyPartNameFeminine:
                return self.arabicFeminineOnes[int(digit)]
            else:
                return self.arabicOnes[int(digit)]
        elif group_level == 0:
            if self.isCurrencyNameFeminine:
                return self.arabicFeminineOnes[int(digit)]
            else:
                return self.arabicOnes[int(digit)]

        else:
            return self.arabicOnes[int(digit)]

    def process_arabic_group(self, group_number, group_level,
                             remaining_number):
        tens = Decimal(group_number) % Decimal(100)
        hundreds = Decimal(group_number) / Decimal(100)
        ret_val = ""

        if int(hundreds) > 0:
            if tens == 0 and int(hundreds) == 2:
                ret_val = "{}".format(self.arabicAppendedTwos[0])
            else:
                ret_val = "{}".format(self.arabicHundreds[int(hundreds)])

        if tens > 0:
            if tens < 20:
                if tens == 2 and int(hundreds) == 0 and group_level > 0:
                    if self.integer_value in [2000, 2000000, 2000000000,
                                              2000000000000, 2000000000000000,
                                              2000000000000000000]:
                        ret_val = "{}".format(
                            self.arabicAppendedTwos[int(group_level)])
                    else:
                        ret_val = "{}".format(
                            self.arabicTwos[int(group_level)])
                else:
                    if ret_val != "":
                        ret_val += " و "

                    if tens == 1 and group_level > 0 and hundreds == 0:
                        ret_val += ""
                    elif (tens == 1 or tens == 2) and (
                            group_level == 0 or group_level == -1) and \
                            hundreds == 0 and remaining_number == 0:
                        ret_val += ""
                    else:
                        ret_val += self.digit_feminine_status(int(tens),
                                                              group_level)
            else:
                print('ones\n\n\n')

                ones = tens % 10
                tens = (tens / 10) - 2
                if ones > 0:
                    if ret_val != "": #Updated 26-10-2022  delete "and tens < 4" condition
                        ret_val += " و "

                    ret_val += self.digit_feminine_status(ones, group_level)
                if ret_val != "" and ones != 0:
                    ret_val += " و "
                if ret_val != "" and ones == 0:   #Updated 26-1-2022
                    ret_val += " و "
                ret_val += self.arabicTens[int(tens)]

        return ret_val

    def convert(self, value):
        self.number = "{:.9f}".format(value)
        self.number_to_arabic(self.arabicPrefixText, self.arabicSuffixText)
        return self.convert_to_arabic()

    def convert_to_arabic(self):
        temp_number = Decimal(self.number)

        if temp_number == Decimal(0):
            return "صفر"

        decimal_string = self.process_arabic_group(self._decimalValue,
                                                   -1,
                                                   Decimal(0))
        ret_val = ""
        group = 0

        while temp_number > Decimal(0):

            number_to_process = int(
                Decimal(str(temp_number)) % Decimal(str(1000)))
            temp_number = int(Decimal(temp_number) / Decimal(1000))

            group_description = \
                self.process_arabic_group(number_to_process,
                                          group,
                                          Decimal(floor(temp_number)))
            if group_description != '':
                if group > 0:
                    if ret_val != "":
                        ret_val = "{} و {}".format("", ret_val)
                    if number_to_process != 2:
                        if number_to_process % 100 != 1:
                            if 3 <= number_to_process <= 10:
                                ret_val = "{} {}".format(
                                    self.arabicPluralGroups[group], ret_val)
                            else:
                                if ret_val != "":
                                    ret_val = "{} {}".format(
                                        self.arabicAppendedGroup[group],
                                        ret_val)
                                else:
                                    ret_val = "{} {}".format(
                                        self.arabicGroup[group], ret_val)

                        else:
                            ret_val = "{} {}".format(self.arabicGroup[group],
                                                     ret_val)
                ret_val = "{} {}".format(group_description, ret_val)
            group += 1
        formatted_number = ""
        if self.arabicPrefixText != "":
            formatted_number += "{} ".format(self.arabicPrefixText)
        formatted_number += ret_val
        if self.integer_value != 0:
            remaining100 = int(self.integer_value % 100)

            if remaining100 == 0:
                formatted_number += self.currency_unit[0]
            elif remaining100 == 1:
                formatted_number += self.currency_unit[0]
            elif remaining100 == 2:
                if self.integer_value == 2:
                    formatted_number += self.currency_unit[1]
                else:
                    formatted_number += self.currency_unit[0]
            elif 3 <= remaining100 <= 10:
                formatted_number += self.currency_unit[2]
            elif 11 <= remaining100 <= 99:
                formatted_number += self.currency_unit[3]
        if self._decimalValue != 0:
            formatted_number += " {} ".format(self.separator)
            formatted_number += decimal_string

        if self._decimalValue != 0:
            formatted_number += " "
            remaining100 = int(self._decimalValue % 100)

            if remaining100 == 0:
                formatted_number += self.currency_subunit[0]
            elif remaining100 == 1:
                formatted_number += self.currency_subunit[0]
            elif remaining100 == 2:
                formatted_number += self.currency_subunit[1]
            elif 3 <= remaining100 <= 10:
                formatted_number += self.currency_subunit[2]
            elif 11 <= remaining100 <= 99:
                formatted_number += self.currency_subunit[3]

        if self.arabicSuffixText != "":
            formatted_number += " {}".format(self.arabicSuffixText)

        return formatted_number

    def validate_number(self, number):
        if number >= self.max_num:
            raise OverflowError(self.errmsg_too_big)
        return number

    def set_currency_prefer(self, currency):
        if currency == 'EGP':
            self.currency_unit = CURRENCY_EGP[0]
            self.currency_subunit = CURRENCY_EGP[1]
        elif currency == 'KWD':
            self.currency_unit = CURRENCY_KWD[0]
            self.currency_subunit = CURRENCY_KWD[1]
        else:
            self.currency_unit = CURRENCY_SR[0]
            self.currency_subunit = CURRENCY_SR[1]

    def to_currency(self, value, currency='SR', prefix='', suffix=''):
        self.set_currency_prefer(currency)
        self.isCurrencyNameFeminine = False
        self.separator = "و"
        self.arabicOnes = ARABIC_ONES
        self.arabicPrefixText = prefix
        self.arabicSuffixText = suffix
        return self.convert(value=value)

    def to_ordinal(self, number, prefix=''):
        if number <= 19:
            return "{}".format(self.arabicOrdinal[number])
        if number < 100:
            self.isCurrencyNameFeminine = True
        else:
            self.isCurrencyNameFeminine = False
        self.currency_subunit = ('', '', '', '')
        self.currency_unit = ('', '', '', '')
        self.arabicPrefixText = prefix
        self.arabicSuffixText = ""
        return "{}".format(self.convert(abs(number)).strip())

    def to_year(self, value):
        value = self.validate_number(value)
        return self.to_cardinal(value)

    def to_ordinal_num(self, value):
        return self.to_ordinal(value).strip()

    def to_cardinal(self, number):
        number = self.validate_number(number)
        minus = ''
        if number < 0:
            minus = 'سالب '
        self.separator = ','
        self.currency_subunit = ('', '', '', '')
        self.currency_unit = ('', '', '', '')
        self.arabicPrefixText = ""
        self.arabicSuffixText = ""
        self.arabicOnes = ARABIC_ONES
        return minus + self.convert(value=abs(number)).strip()
