"""
NetSentry - OUI (Organizationally Unique Identifier) Database
Provides offline MAC address vendor lookup using an embedded dictionary.
Covers the most common ~2000 OUI prefixes from IEEE MA-L registry.
"""

import logging

logger = logging.getLogger("netsentry.oui")


# Embedded OUI database - maps MAC prefix (first 3 bytes) to vendor name
# This covers the most common network device manufacturers
# Format: "AABBCC" -> "Vendor Name"
OUI_DATABASE = {
    # Key Modern Device Vendors & Mesh Networking
    "202351": "TP-Link", "A86E84": "TP-Link", "50D4F7": "TP-Link", "B04E26": "TP-Link",
    "30DE4B": "TP-Link", "60A44C": "TP-Link", "003192": "TP-Link", "74DA38": "TP-Link",
    "AC84C6": "TP-Link", "B48655": "TP-Link", "CC32E5": "TP-Link", "EC086B": "TP-Link",
    "14CC20": "TP-Link", "18D6C7": "TP-Link", "D80D17": "TP-Link", "98DED0": "TP-Link",
    "002586": "TP-Link", "10FEED": "TP-Link", "1C3BF3": "TP-Link", "54AF97": "TP-Link",
    "704F57": "TP-Link", "84D81B": "TP-Link", "90F652": "TP-Link", "C006C3": "TP-Link",

    # IoT / Smart Home / ESP Microcontrollers
    "E08CFE": "Espressif", "3844BE": "Espressif", "24D7EB": "Espressif", "30AEA4": "Espressif",
    "240AC4": "Espressif", "A4CF12": "Espressif", "84F3EB": "Espressif", "807D3A": "Espressif",
    "48E729": "Espressif", "40F520": "Espressif", "3C71BF": "Espressif", "246F28": "Espressif",
    "18FE34": "Espressif", "083A88": "Espressif", "B4E62D": "Espressif", "BCDD26": "Espressif",
    "AC67B2": "Espressif", "CC50E3": "Espressif", "94B97E": "Espressif", "4C11AE": "Espressif",

    # Smart Thermostats / Ecobee
    "446132": "Ecobee", "001558": "Ecobee", "B86C4B": "Ecobee",

    # Printers & Imaging
    "200B74": "Canon", "70820E": "Canon", "000085": "Canon", "180C11": "Canon",
    "84BA3B": "Canon", "B827EB": "Canon", "D48564": "Canon", "001E8F": "Canon",
    "002673": "Epson", "64EB8C": "Epson", "AC1406": "Epson",
    "001BA9": "Brother", "30055C": "Brother", "008077": "Brother",

    # Smart TVs / Media Streamers
    "F02F9E": "Samsung", "E8508B": "Samsung", "D003DF": "Samsung", "508569": "Samsung",
    "24F5AA": "Samsung", "F40F24": "Samsung", "A475B9": "Samsung", "549759": "Samsung",
    "842519": "Samsung", "BC1485": "Samsung", "34C9F0": "Samsung", "78471D": "Samsung",
    "28AF42": "Roku", "D83134": "Roku", "B0A737": "Roku", "ACAE19": "Roku",
    "84EA99": "Roku", "788A20": "Roku", "20DFB9": "Roku", "DC3A5E": "Roku",
    "00041F": "Sony", "0013A9": "Sony", "0015C1": "Sony", "0019C5": "Sony",
    "001D0D": "Sony", "00248D": "Sony", "0498F3": "Sony", "086BD9": "Sony",
    "001C62": "LG", "10F9EE": "LG", "203DB0": "LG", "A823FE": "LG",

    # Voice Assistants & Smart Home
    "4C5739": "Amazon", "FC65DE": "Amazon", "68545A": "Amazon", "44650D": "Amazon",
    "3894ED": "Amazon", "40B4CD": "Amazon", "0C47C9": "Amazon", "18742E": "Amazon",
    "34D270": "Amazon", "50F5DA": "Amazon", "74C246": "Amazon", "84D6D0": "Amazon",
    "54F29F": "Tuya", "D4A651": "Tuya", "A09208": "Tuya", "1097BD": "Tuya",
    "70039F": "Tuya", "68572D": "Tuya", "20F41B": "Tuya",
    "B8D61A": "Pura",
    "000E58": "Sonos", "347E5C": "Sonos", "48A6B8": "Sonos", "5C313E": "Sonos",
    "7828CA": "Sonos", "949F3E": "Sonos", "B8E937": "Sonos", "C43875": "Sonos",

    # PC / Mobile / Networking
    "04ECD8": "HP", "9C50EE": "HP", "3CD92B": "HP", "28D244": "HP",
    "001E0B": "HP", "00215A": "HP", "002481": "HP", "0025B3": "HP",
    "54EE75": "Lenovo", "8CEE28": "Lenovo", "002B67": "Lenovo", "70723C": "Lenovo", "AC3870": "Lenovo",
    "001A79": "Intel", "001E67": "Intel", "3413E8": "Intel", "8086F2": "Intel",
    "001422": "Dell", "180373": "Dell", "24B6FD": "Dell", "B8AC6F": "Dell",
    "0009B0": "Google", "546009": "Google", "D86C63": "Google", "F4F5D8": "Google",
    "F4032C": "Google", "E4F042": "Google", "A47733": "Google", "949B2C": "Google",
    "4827EA": "Fn-Link", "28D127": "Fn-Link",
    "387C76": "Apple", "88E712": "Apple", "4089C6": "Apple", "444201": "Apple",

    # Apple
    "00A040": "Apple", "000393": "Apple", "000502": "Apple",
    "000A27": "Apple", "000A95": "Apple", "000D93": "Apple",
    "001124": "Apple", "001451": "Apple", "0016CB": "Apple",
    "0017F2": "Apple", "0019E3": "Apple", "001B63": "Apple",
    "001CB3": "Apple", "001D4F": "Apple", "001E52": "Apple",
    "001F5B": "Apple", "001FF3": "Apple", "0021E9": "Apple",
    "002241": "Apple", "002312": "Apple", "002436": "Apple",
    "002500": "Apple", "002608": "Apple", "00264A": "Apple",
    "002776": "Apple", "003065": "Apple", "003EE1": "Apple",
    "0050E4": "Apple", "0056CD": "Apple", "006171": "Apple",
    "006D52": "Apple", "00F4B9": "Apple", "00F76F": "Apple",
    "040CCE": "Apple", "041552": "Apple", "042665": "Apple",
    "044BED": "Apple", "04489A": "Apple", "0452F3": "Apple",
    "04D3CF": "Apple", "04E536": "Apple", "04F13E": "Apple",
    "04F7E4": "Apple", "080007": "Apple", "0C4DE9": "Apple",
    "0C7760": "Apple", "0CBC9F": "Apple", "0CD746": "Apple",
    "10417F": "Apple", "1093E9": "Apple", "10DDB1": "Apple",
    "14109F": "Apple", "149906": "Apple", "14205E": "Apple",
    "148FC6": "Apple", "18AF8F": "Apple", "18E7F4": "Apple",
    "1C1AC0": "Apple", "1C36BB": "Apple", "1C5CF2": "Apple",
    "1C9148": "Apple", "20768F": "Apple", "20A2E4": "Apple",
    "209BCD": "Apple", "24240E": "Apple", "24A074": "Apple",
    "24A2E1": "Apple", "24AB81": "Apple", "24F094": "Apple",
    "280B5C": "Apple", "2837E2": "Apple", "285AEB": "Apple",
    "286AB8": "Apple", "28A02B": "Apple", "28CF03": "Apple",
    "28CFE9": "Apple", "28E14C": "Apple", "28E7CF": "Apple",
    "28F076": "Apple", "2C200B": "Apple", "2CB43A": "Apple",
    "2CF0A2": "Apple", "2CF0EE": "Apple", "30636B": "Apple",
    "3090AB": "Apple", "30F7C5": "Apple", "3408BC": "Apple",
    "34363B": "Apple", "34A395": "Apple", "34C059": "Apple",
    "34E2FD": "Apple", "380F4A": "Apple", "3871DE": "Apple",
    "38484C": "Apple", "38B54D": "Apple", "38C986": "Apple",
    "3C0754": "Apple", "3C15C2": "Apple", "3CD0F8": "Apple",
    "3CE072": "Apple", "40331A": "Apple", "403004": "Apple",
    "40A6D9": "Apple", "40B395": "Apple", "40D32D": "Apple",
    "44D884": "Apple", "4827EA": "Apple", "484BAA": "Apple",
    "48746E": "Apple", "48A195": "Apple", "48BF6B": "Apple",
    "48D705": "Apple", "48E9F1": "Apple", "4C3275": "Apple",
    "4C7C5F": "Apple", "4C8D79": "Apple", "4CBCA5": "Apple",
    "501AC5": "Apple", "5043AB": "Apple", "507A55": "Apple",
    "50EAD6": "Apple", "541354": "Apple", "5440AD": "Apple",
    "5477F3": "Apple", "549F13": "Apple", "54AE27": "Apple",
    "54E43A": "Apple", "54EAA8": "Apple", "5855CA": "Apple",
    "58B035": "Apple", "5C5948": "Apple", "5C8D4E": "Apple",
    "5C969D": "Apple", "5CADCF": "Apple", "5CF5DA": "Apple",
    "5CF7E6": "Apple", "60C547": "Apple", "60D9C7": "Apple",
    "60F445": "Apple", "60FA86": "Apple", "60FB42": "Apple",
    "60FEC5": "Apple", "64200C": "Apple", "6476BA": "Apple",
    "649ABE": "Apple", "64A3CB": "Apple", "64B0A6": "Apple",
    "64E682": "Apple", "680927": "Apple", "685B35": "Apple",
    "685D43": "Apple", "6896A3": "Apple", "68967B": "Apple",
    "68A86D": "Apple", "68AE20": "Apple", "68D93C": "Apple",
    "68DBCA": "Apple", "68FEF7": "Apple", "6C19C0": "Apple",
    "6C4008": "Apple", "6C709F": "Apple", "6C72E7": "Apple",
    "6C94F8": "Apple", "6CC26B": "Apple", "700DEF": "Apple",
    "708B4E": "Apple", "7081EB": "Apple", "70DEE2": "Apple",
    "70ECE4": "Apple", "70F087": "Apple", "723EAA": "Apple",
    "7440DB": "Apple", "748114": "Apple", "748D08": "Apple",
    "749EAF": "Apple", "74E1B6": "Apple", "74E2F5": "Apple",
    "783A84": "Apple", "786C1C": "Apple", "7867D7": "Apple",
    "78886D": "Apple", "789F70": "Apple", "78A3E4": "Apple",
    "78CA39": "Apple", "78D75F": "Apple", "78FD94": "Apple",
    "7C0191": "Apple", "7C11BE": "Apple", "7C5049": "Apple",
    "7C6DF8": "Apple", "7CC3A1": "Apple", "7CD1C3": "Apple",
    "7CF05F": "Apple", "7CFADF": "Apple", "802154": "Apple",
    "804971": "Apple", "80006E": "Apple", "80929F": "Apple",
    "80BE05": "Apple", "80E650": "Apple", "80EA96": "Apple",
    "80ED2C": "Apple", "843835": "Apple", "848506": "Apple",
    "8488F8": "Apple", "848E0C": "Apple", "84A134": "Apple",
    "84B153": "Apple", "84FCAC": "Apple", "84FCFE": "Apple",
    "881FA1": "Apple", "886B6E": "Apple", "88C663": "Apple",
    "88CB87": "Apple", "88E87F": "Apple", "8C006D": "Apple",
    "8C2937": "Apple", "8C2DAA": "Apple", "8C5877": "Apple",
    "8C7B9D": "Apple", "8C8590": "Apple", "8C8FE9": "Apple",
    "8CFABA": "Apple", "903C92": "Apple", "9060F1": "Apple",
    "90840D": "Apple", "90B21F": "Apple", "90B931": "Apple",
    "90C1C6": "Apple", "90FD61": "Apple", "944452": "Apple",
    "9801A7": "Apple", "9803D8": "Apple", "98B8E3": "Apple",
    "98D6BB": "Apple", "98E0D9": "Apple", "98F0AB": "Apple",
    "98FE94": "Apple", "9C04EB": "Apple", "9C207B": "Apple",
    "9C293F": "Apple", "9C35EB": "Apple", "9C4FDA": "Apple",
    "9C84B6": "Apple", "9CF387": "Apple", "9CF48E": "Apple",
    "A01828": "Apple", "A0999B": "Apple", "A0D795": "Apple",
    "A0EDCD": "Apple", "A43135": "Apple", "A45E60": "Apple",
    "A46706": "Apple", "A4B197": "Apple", "A4C361": "Apple",
    "A4D18C": "Apple", "A4D1D2": "Apple", "A4F1E8": "Apple",
    "A82066": "Apple", "A85B78": "Apple", "A860B6": "Apple",
    "A886DD": "Apple", "A88808": "Apple", "A8667F": "Apple",
    "A896C6": "Apple", "A8FAD8": "Apple", "AC293A": "Apple",
    "ACBC32": "Apple", "ACFDEC": "Apple", "B03495": "Apple",
    "B065BD": "Apple", "B09FBA": "Apple", "B0702D": "Apple",
    "B48B19": "Apple", "B4F0AB": "Apple", "B8098A": "Apple",
    "B817C2": "Apple", "B844D9": "Apple", "B88D12": "Apple",
    "B8C111": "Apple", "B8E856": "Apple", "B8F6B1": "Apple",
    "B8FF61": "Apple", "BC3BAF": "Apple", "BC5436": "Apple",
    "BC6778": "Apple", "BC9FEF": "Apple", "BCA920": "Apple",
    "BCE143": "Apple", "BCF5AC": "Apple", "C01ADA": "Apple",
    "C0847A": "Apple", "C09F42": "Apple", "C0B658": "Apple",
    "C0CCDB": "Apple", "C0D012": "Apple", "C42C03": "Apple",
    "C4B301": "Apple", "C81EE7": "Apple", "C82A14": "Apple",
    "C869CD": "Apple", "C86F1D": "Apple", "C8334B": "Apple",
    "C83C85": "Apple", "C8B5B7": "Apple", "C8BCC8": "Apple",
    "C8D083": "Apple", "CC088D": "Apple", "CC2DB7": "Apple",
    "CC4463": "Apple", "CC785F": "Apple", "CCE1D5": "Apple",
    "D023DB": "Apple", "D02598": "Apple", "D03311": "Apple",
    "D04F7E": "Apple", "D0A637": "Apple", "D0C5F3": "Apple",
    "D0D2B0": "Apple", "D0E140": "Apple", "D41A3F": "Apple",
    "D4619D": "Apple", "D49A20": "Apple", "D4F46F": "Apple",
    "D81D72": "Apple", "D83062": "Apple", "D89695": "Apple",
    "D89E3F": "Apple", "D8A25E": "Apple", "D8BB2C": "Apple",
    "D8CF9C": "Apple", "DC0C5C": "Apple", "DC2B2A": "Apple",
    "DC2B61": "Apple", "DC3714": "Apple", "DC415F": "Apple",
    "DC56E7": "Apple", "DC86D8": "Apple", "DC9B9C": "Apple",
    "DCA4CA": "Apple", "DCA904": "Apple", "E05F45": "Apple",
    "E06678": "Apple", "E0AC CB": "Apple", "E0B52D": "Apple",
    "E0C767": "Apple", "E0C97A": "Apple", "E0F5C6": "Apple",
    "E425E7": "Apple", "E48B7F": "Apple", "E49ADC": "Apple",
    "E4C63D": "Apple", "E4CE8F": "Apple", "E4E0A6": "Apple",
    "E8040B": "Apple", "E80688": "Apple", "E8802E": "Apple",
    "E88D28": "Apple", "E8B2AC": "Apple", "EC3586": "Apple",
    "EC852F": "Apple", "F02475": "Apple", "F04F7C": "Apple",
    "F0989D": "Apple", "F0B479": "Apple", "F0C1F1": "Apple",
    "F0D1A9": "Apple", "F0DBE2": "Apple", "F0DCE2": "Apple",
    "F40F24": "Apple", "F41BA1": "Apple", "F431C3": "Apple",
    "F45C89": "Apple", "F4F15A": "Apple", "F4F951": "Apple",
    "F81EDF": "Apple", "F82793": "Apple", "F86214": "Apple",
    "FC253F": "Apple", "FCFC48": "Apple",

    # Samsung
    "002567": "Samsung", "0007AB": "Samsung", "000D25": "Samsung",
    "000FBB": "Samsung", "0012FB": "Samsung", "00166B": "Samsung",
    "00166C": "Samsung", "001777": "Samsung", "001832": "Samsung",
    "001A8A": "Samsung", "001B98": "Samsung", "001CE6": "Samsung",
    "001DF2": "Samsung", "001EAE": "Samsung", "001EE1": "Samsung",
    "001EE2": "Samsung", "001FCC": "Samsung", "001FCD": "Samsung",
    "002119": "Samsung", "002399": "Samsung", "0024E9": "Samsung",
    "002566": "Samsung", "002637": "Samsung", "0026E2": "Samsung",
    "002806": "Samsung", "0C8910": "Samsung", "100BA9": "Samsung",
    "1077B1": "Samsung", "141F78": "Samsung", "14568E": "Samsung",
    "1489FD": "Samsung", "149F3C": "Samsung", "14A364": "Samsung",
    "14BB6E": "Samsung", "181EB0": "Samsung", "1816C9": "Samsung",
    "18227E": "Samsung", "183A2D": "Samsung", "183F47": "Samsung",
    "18673B": "Samsung", "188331": "Samsung", "18895B": "Samsung",
    "1C62B8": "Samsung", "1C66AA": "Samsung", "2013E0": "Samsung",
    "200DB0": "Samsung", "2481A7": "Samsung", "2484AD": "Samsung",
    "24920E": "Samsung", "24C696": "Samsung", "24DB96": "Samsung",
    "282CB2": "Samsung", "28987B": "Samsung", "2C4401": "Samsung",
    "30CBF8": "Samsung", "30D6C9": "Samsung", "3423BA": "Samsung",
    "3442A4": "Samsung", "34AA8B": "Samsung", "34C3AC": "Samsung",
    "380195": "Samsung", "381A52": "Samsung", "383A21": "Samsung",
    "38D40B": "Samsung", "38ECE4": "Samsung", "3C5A37": "Samsung",
    "3C62F0": "Samsung", "3C8BFE": "Samsung", "3CE0D0": "Samsung",
    "400E85": "Samsung", "40D3AE": "Samsung", "44783E": "Samsung",
    "44F459": "Samsung", "481A84": "Samsung", "489D24": "Samsung",
    "48C796": "Samsung", "4CA56D": "Samsung", "50017F": "Samsung",
    "503275": "Samsung", "50A4C8": "Samsung", "50B7C3": "Samsung",
    "50F520": "Samsung", "5440AD": "Samsung", "544E90": "Samsung",
    "549B12": "Samsung", "54880E": "Samsung", "5802EF": "Samsung",
    "581F28": "Samsung", "587F57": "Samsung", "5CA39D": "Samsung",
    "5CE8EB": "Samsung", "606BBD": "Samsung", "609866": "Samsung",
    "6077E2": "Samsung", "60AF6D": "Samsung", "641316": "Samsung",
    "64B853": "Samsung", "684898": "Samsung", "6CB7F4": "Samsung",
    "70F927": "Samsung", "7440BB": "Samsung", "747548": "Samsung",
    "748F1B": "Samsung", "749DDC": "Samsung", "74E543": "Samsung",
    "7811DC": "Samsung", "78005D": "Samsung", "78471D": "Samsung",
    "78520F": "Samsung", "78A873": "Samsung", "78F882": "Samsung",
    "80656D": "Samsung", "8425DB": "Samsung", "842519": "Samsung",
    "843838": "Samsung", "84119E": "Samsung", "845181": "Samsung",
    "8455A5": "Samsung", "849866": "Samsung", "84A466": "Samsung",
    "88329B": "Samsung", "8867B2": "Samsung", "886B0F": "Samsung",
    "8C7116": "Samsung", "8CC8CD": "Samsung", "907004": "Samsung",
    "90B134": "Samsung", "94350A": "Samsung", "94D771": "Samsung",
    "94E345": "Samsung", "980C82": "Samsung", "9852B1": "Samsung",
    "98568C": "Samsung", "983B16": "Samsung", "986001": "Samsung",
    "988389": "Samsung", "98FD74": "Samsung", "9C02B1": "Samsung",
    "9C3AAF": "Samsung", "9C6ABE": "Samsung", "A007B6": "Samsung",
    "A00798": "Samsung", "A07591": "Samsung", "A468BC": "Samsung",
    "A48431": "Samsung", "A4EBD3": "Samsung", "A80600": "Samsung",
    "A8F274": "Samsung", "AC3613": "Samsung", "AC5A14": "Samsung",
    "ACE4EC": "Samsung", "B407F9": "Samsung", "B47443": "Samsung",
    "B49D0B": "Samsung", "B4EF39": "Samsung", "B8D9CE": "Samsung",
    "B85510": "Samsung", "BC1485": "Samsung", "BC3AEA": "Samsung",
    "BC4486": "Samsung", "BC7ABF": "Samsung", "BCA8A6": "Samsung",
    "C0B6F9": "Samsung", "C0D3C0": "Samsung", "C44619": "Samsung",
    "C45006": "Samsung", "C47DCC": "Samsung", "C4731E": "Samsung",
    "C8BA94": "Samsung", "CC07AB": "Samsung", "D022BE": "Samsung",
    "D06F4A": "Samsung", "D0667B": "Samsung", "D0C1B1": "Samsung",
    "D0DFC7": "Samsung", "D0DFD6": "Samsung", "D4878B": "Samsung",
    "D49CB5": "Samsung", "D4A9A7": "Samsung", "D4E8B2": "Samsung",
    "D8578E": "Samsung", "D8901D": "Samsung", "D8C4E9": "Samsung",
    "DC7144": "Samsung", "DCEB69": "Samsung", "DCEF09": "Samsung",
    "E0B9A5": "Samsung", "E0CBBC": "Samsung", "E0DB10": "Samsung",
    "E0E0FC": "Samsung", "E439D8": "Samsung", "E440E2": "Samsung",
    "E45D75": "Samsung", "E458B8": "Samsung", "E4B021": "Samsung",
    "E83935": "Samsung", "E8E5D6": "Samsung", "EC107B": "Samsung",
    "EC1F72": "Samsung", "ECAA25": "Samsung", "ECD09F": "Samsung",
    "F008F1": "Samsung", "F04347": "Samsung", "F0251C": "Samsung",
    "F025B7": "Samsung", "F05A09": "Samsung", "F0728C": "Samsung",
    "F0E77E": "Samsung", "F40E22": "Samsung", "F44D30": "Samsung",
    "F4428F": "Samsung", "F49F54": "Samsung", "F4D9FB": "Samsung",
    "F80CF3": "Samsung", "F81D78": "Samsung", "F84897": "Samsung",
    "F86CBE": "Samsung", "F8D0BD": "Samsung", "FC1910": "Samsung",
    "FC4203": "Samsung", "FCA13E": "Samsung", "FCC233": "Samsung",

    # Intel
    "000347": "Intel", "0003FE": "Intel", "000732": "Intel",
    "000CF1": "Intel", "000E0C": "Intel", "000E35": "Intel",
    "001111": "Intel", "00128F": "Intel", "001302": "Intel",
    "001320": "Intel", "001395": "Intel", "0013CE": "Intel",
    "0013E8": "Intel", "001500": "Intel", "001517": "Intel",
    "001676": "Intel", "001695": "Intel", "0016EA": "Intel",
    "0016EB": "Intel", "001820": "Intel", "001DE0": "Intel",
    "001E64": "Intel", "001E65": "Intel", "001E67": "Intel",
    "001F3B": "Intel", "001F3C": "Intel", "002128": "Intel",
    "002219": "Intel", "002264": "Intel", "0022FA": "Intel",
    "0022FB": "Intel", "002314": "Intel", "002315": "Intel",
    "002614": "Intel", "00270E": "Intel", "002710": "Intel",
    "0050F1": "Intel", "3C970E": "Intel", "40A3CC": "Intel",
    "44032C": "Intel", "48D224": "Intel", "502DA2": "Intel",
    "5CC5D4": "Intel", "685D43": "Intel", "6C8814": "Intel",
    "7C7A91": "Intel", "80861A": "Intel", "84C1C1": "Intel",
    "88B111": "Intel", "8C8D28": "Intel", "908D6C": "Intel",
    "98541B": "Intel", "9C4E36": "Intel", "A0481C": "Intel",
    "A4C494": "Intel", "B4D5BD": "Intel", "B4E1C4": "Intel",
    "B8A386": "Intel", "C43655": "Intel", "C8D3FF": "Intel",
    "CC2F71": "Intel", "D0E782": "Intel", "D8FC93": "Intel",
    "E0D55E": "Intel", "E828C1": "Intel", "EC0EC4": "Intel",
    "F01FAF": "Intel", "F04DA2": "Intel", "F077C3": "Intel",
    "F48C50": "Intel", "F8B156": "Intel", "FC774A": "Intel",

    # TP-Link
    "001D0F": "TP-Link", "0023CD": "TP-Link", "002719": "TP-Link",
    "009F28": "TP-Link", "083E0C": "TP-Link", "10FEED": "TP-Link",
    "14CC20": "TP-Link", "14CF92": "TP-Link", "18A6F7": "TP-Link",
    "18D6C7": "TP-Link", "1CEA1B": "TP-Link", "2077B0": "TP-Link",
    "24693E": "TP-Link", "305A3A": "TP-Link", "30B5C2": "TP-Link",
    "3C52A1": "TP-Link", "40169F": "TP-Link", "503EAA": "TP-Link",
    "5091E3": "TP-Link", "50BD5F": "TP-Link", "54C80F": "TP-Link",
    "5CE928": "TP-Link", "60E327": "TP-Link", "647002": "TP-Link",
    "68FF7B": "TP-Link", "6C5AB0": "TP-Link", "70F11C": "TP-Link",
    "74DA38": "TP-Link", "7844FD": "TP-Link", "78443C": "TP-Link",
    "7C8BCA": "TP-Link", "84D82B": "TP-Link", "88253B": "TP-Link",
    "8C210A": "TP-Link", "900A39": "TP-Link", "94D9B3": "TP-Link",
    "981E0F": "TP-Link", "98DA49": "TP-Link", "A091CD": "TP-Link",
    "A842A1": "TP-Link", "AC84C6": "TP-Link", "B02427": "TP-Link",
    "B0A7B9": "TP-Link", "B09575": "TP-Link", "B8D7AF": "TP-Link",
    "C025A2": "TP-Link", "C0E42D": "TP-Link", "C43ABE": "TP-Link",
    "C46E1F": "TP-Link", "CC32E5": "TP-Link", "CCFB65": "TP-Link",
    "D460E3": "TP-Link", "D46E0E": "TP-Link", "D8472B": "TP-Link",
    "D850E6": "TP-Link", "DC569A": "TP-Link", "E005C5": "TP-Link",
    "E4C3CA": "TP-Link", "E894F6": "TP-Link", "EC086B": "TP-Link",
    "EC172F": "TP-Link", "EC888F": "TP-Link", "F01987": "TP-Link",
    "F481A0": "TP-Link", "F4EC38": "TP-Link", "F4F26D": "TP-Link",
    "F8D111": "TP-Link",

    # Google
    "001A11": "Google", "3C5AB4": "Google", "54601D": "Google",
    "943826": "Google", "A47733": "Google", "F4F5DB": "Google",
    "F4F5E8": "Google", "F4F5D8": "Google", "DCA632": "Google",

    # Amazon
    "0C47C9": "Amazon", "10CE2B": "Amazon", "1CAB3F": "Amazon",
    "38F73D": "Amazon", "40A2DB": "Amazon", "440049": "Amazon",
    "50DCE7": "Amazon", "50F5DA": "Amazon", "68372B": "Amazon",
    "68543D": "Amazon", "6854FD": "Amazon", "74C246": "Amazon",
    "747548": "Amazon", "784F43": "Amazon", "84D64B": "Amazon",
    "9031CD": "Amazon", "A002DC": "Amazon", "AC63BE": "Amazon",
    "B47C9C": "Amazon", "C8A2CE": "Amazon", "CC9E00": "Amazon",
    "F0272D": "Amazon", "F0D2F1": "Amazon", "FCA183": "Amazon",
    "FCC2DE": "Amazon", "FEF73A": "Amazon",

    # Netgear
    "00146C": "Netgear", "001B2F": "Netgear", "001E2A": "Netgear",
    "001F33": "Netgear", "002636": "Netgear", "00269E": "Netgear",
    "008EF2": "Netgear", "08028E": "Netgear", "100D7F": "Netgear",
    "100C6B": "Netgear", "1C3BF3": "Netgear", "204E7F": "Netgear",
    "20E52A": "Netgear", "280564": "Netgear", "2CB05D": "Netgear",
    "30469A": "Netgear", "3894ED": "Netgear", "3C3786": "Netgear",
    "4494FC": "Netgear", "44A56E": "Netgear", "4C60DE": "Netgear",
    "6038E0": "Netgear", "6CB0CE": "Netgear", "744401": "Netgear",
    "7C8BCA": "Netgear", "800D8C": "Netgear", "8434DA": "Netgear",
    "84A423": "Netgear", "84A650": "Netgear", "8C04BA": "Netgear",
    "9CC9EB": "Netgear", "A00460": "Netgear", "A021B7": "Netgear",
    "A42B8C": "Netgear", "B03956": "Netgear", "B07FB9": "Netgear",
    "C43DC7": "Netgear", "C4046F": "Netgear", "C8B4A0": "Netgear",
    "DC9FDB": "Netgear", "E0469A": "Netgear", "E0912B": "Netgear",
    "E4F4C6": "Netgear", "E8EAB0": "Netgear", "F87394": "Netgear",

    # ASUS / ASUSTek
    "000C6E": "ASUS", "000E09": "ASUS", "001731": "ASUS",
    "001A92": "ASUS", "001BFC": "ASUS", "001D60": "ASUS",
    "001E8C": "ASUS", "002354": "ASUS", "002618": "ASUS",
    "049226": "ASUS", "08606E": "ASUS", "086266": "ASUS",
    "107B44": "ASUS", "10BF48": "ASUS", "10C37B": "ASUS",
    "14DAE9": "ASUS", "1831BF": "ASUS", "1C872C": "ASUS",
    "244BFE": "ASUS", "2C56DC": "ASUS", "2CFDA1": "ASUS",
    "305A3A": "ASUS", "3085A9": "ASUS", "3497F6": "ASUS",
    "382C4A": "ASUS", "38D547": "ASUS", "40167E": "ASUS",
    "40B076": "ASUS", "485B39": "ASUS", "4CEDFB": "ASUS",
    "504E69": "ASUS", "54044A": "ASUS", "581244": "ASUS",
    "6045CB": "ASUS", "60A44C": "ASUS", "706655": "ASUS",
    "74D02B": "ASUS", "787863": "ASUS", "8C89A5": "ASUS",
    "9C5C8E": "ASUS", "A036BC": "ASUS", "A4BF01": "ASUS",
    "AC220B": "ASUS", "B06EBF": "ASUS", "BC5FF4": "ASUS",
    "C87F54": "ASUS", "D017C2": "ASUS", "D45D64": "ASUS",
    "D850E6": "ASUS", "E03F49": "ASUS", "E0CB4E": "ASUS",
    "F07959": "ASUS", "F46D04": "ASUS", "F832E4": "ASUS",

    # Dell
    "001422": "Dell", "001882": "Dell", "001A4A": "Dell",
    "001D09": "Dell", "001E4F": "Dell", "0021701": "Dell",
    "002219": "Dell", "002264": "Dell", "00248C": "Dell",
    "002514": "Dell", "0026B9": "Dell", "00B0D0": "Dell",
    "00C04F": "Dell", "10604B": "Dell", "10986C": "Dell",
    "143429": "Dell", "149316": "Dell", "149ED6": "Dell",
    "18037D": "Dell", "18A99B": "Dell", "1C40E8": "Dell",
    "204747": "Dell", "24B6FD": "Dell", "28F10E": "Dell",
    "34E6D7": "Dell", "484D7E": "Dell", "509A4C": "Dell",
    "54BF64": "Dell", "5C260A": "Dell", "64006A": "Dell",
    "7C6920": "Dell", "8048EB": "Dell", "842B2B": "Dell",
    "843A5B": "Dell", "90B11C": "Dell", "984BE1": "Dell",
    "A41F72": "Dell", "A4BADB": "Dell", "B083FE": "Dell",
    "B885A4": "Dell", "B8CA3A": "Dell", "BC3011": "Dell",
    "C81F66": "Dell", "D048E7": "Dell", "D4AE52": "Dell",
    "D4BE38": "Dell", "D89E3F": "Dell", "E0DB55": "Dell",
    "F04DA2": "Dell", "F48E38": "Dell", "F8B156": "Dell",
    "F8BC12": "Dell", "F8DB88": "Dell",

    # Hewlett-Packard / HP
    "000802": "HP", "000A57": "HP", "000BCD": "HP",
    "000D9D": "HP", "000EB3": "HP", "000F20": "HP",
    "001083": "HP", "0010E3": "HP", "001185": "HP",
    "001279": "HP", "001321": "HP", "001438": "HP",
    "0017A4": "HP", "001871": "HP", "0019BB": "HP",
    "001A4B": "HP", "001B78": "HP", "001CC4": "HP",
    "001E0B": "HP", "001F29": "HP", "002128": "HP",
    "002481": "HP", "0025B3": "HP", "002655": "HP",
    "0030C1": "HP", "003048": "HP", "00306E": "HP",
    "005080": "HP", "009C02": "HP", "0A0027": "HP",
    "10604B": "HP", "10E68A": "HP", "14022E": "HP",
    "1458D0": "HP", "14588B": "HP", "1CC1DE": "HP",
    "2001A6": "HP", "28924A": "HP", "308D99": "HP",
    "380025": "HP", "3C4A92": "HP", "3C61FA": "HP",
    "3CA82A": "HP", "40B034": "HP", "4CE139": "HP",
    "50EB56": "HP", "58AC78": "HP", "5CB901": "HP",
    "64511E": "HP", "642737": "HP", "6805CA": "HP",
    "6C3BE5": "HP", "70106F": "HP", "78E3B5": "HP",
    "7CC5B2": "HP", "80A589": "HP", "80CE62": "HP",
    "844BF5": "HP", "8851FB": "HP", "8C19B5": "HP",
    "9457A5": "HP", "9CB654": "HP", "A036BC": "HP",
    "A06E6F": "HP", "A45D36": "HP", "B05ADA": "HP",
    "B499BA": "HP", "B8AF67": "HP", "BC4577": "HP",
    "C4346B": "HP", "C8CBB8": "HP", "CC3D82": "HP",
    "D076E1": "HP", "D48564": "HP", "D4C94B": "HP",
    "D4E3C0": "HP", "D8D385": "HP", "DC4A3E": "HP",
    "E4115B": "HP", "E8F724": "HP", "EC8EB5": "HP",
    "F0921C": "HP", "F4CE46": "HP", "F8B46A": "HP",

    # Xiaomi
    "0C1DAF": "Xiaomi", "100D32": "Xiaomi", "1420E9": "Xiaomi",
    "182274": "Xiaomi", "20F4FB": "Xiaomi", "28E31F": "Xiaomi",
    "2C574B": "Xiaomi", "2C957F": "Xiaomi", "342D4D": "Xiaomi",
    "34CE00": "Xiaomi", "380728": "Xiaomi", "38A4ED": "Xiaomi",
    "3CB87A": "Xiaomi", "50EC50": "Xiaomi", "58446D": "Xiaomi",
    "5CC307": "Xiaomi", "640980": "Xiaomi", "6447E0": "Xiaomi",
    "64B473": "Xiaomi", "7451BA": "Xiaomi", "749D79": "Xiaomi",
    "74F61C": "Xiaomi", "7802B7": "Xiaomi", "78110D": "Xiaomi",
    "78D2BF": "Xiaomi", "8041B0": "Xiaomi", "80AD16": "Xiaomi",
    "842170": "Xiaomi", "84F3EB": "Xiaomi", "8CB8EB": "Xiaomi",
    "90740C": "Xiaomi", "9C5CF9": "Xiaomi", "9C99A0": "Xiaomi",
    "A086C6": "Xiaomi", "A462F8": "Xiaomi", "AC83F3": "Xiaomi",
    "B0D59D": "Xiaomi", "B423B6": "Xiaomi", "C40B69": "Xiaomi",
    "C46AB7": "Xiaomi", "CC53B5": "Xiaomi", "D4970B": "Xiaomi",
    "D8F30C": "Xiaomi", "E4462F": "Xiaomi", "E8AB73": "Xiaomi",
    "EC1B12": "Xiaomi", "ECBE5B": "Xiaomi", "F04A02": "Xiaomi",
    "F0B429": "Xiaomi", "F48B32": "Xiaomi", "F8A45F": "Xiaomi",
    "FCD733": "Xiaomi",

    # Microsoft
    "000D3A": "Microsoft", "001DD8": "Microsoft", "002707": "Microsoft",
    "0050F2": "Microsoft", "2816AD": "Microsoft", "3CE1A1": "Microsoft",
    "48ED73": "Microsoft", "50F4EB": "Microsoft", "58DF42": "Microsoft",
    "5C5188": "Microsoft", "601E28": "Microsoft", "7C1E52": "Microsoft",
    "80EF20": "Microsoft", "84A93E": "Microsoft", "9801A7": "Microsoft",
    "B4D5BD": "Microsoft", "B8D7AF": "Microsoft", "C0C6A6": "Microsoft",
    "C83F26": "Microsoft", "D42C44": "Microsoft", "D48564": "Microsoft",
    "DC537C": "Microsoft", "E05042": "Microsoft",

    # Cisco
    "000142": "Cisco", "000163": "Cisco", "000164": "Cisco",
    "000196": "Cisco", "000A41": "Cisco", "000A42": "Cisco",
    "000B46": "Cisco", "000B85": "Cisco", "000D65": "Cisco",
    "000D66": "Cisco", "000DBC": "Cisco", "000DBD": "Cisco",
    "000DE4": "Cisco", "000DE5": "Cisco", "000FEF": "Cisco",
    "00107B": "Cisco", "001195": "Cisco", "00121E": "Cisco",
    "0012DA": "Cisco", "0013C4": "Cisco", "001443": "Cisco",
    "0015C6": "Cisco", "0015C7": "Cisco", "0015FA": "Cisco",
    "001642": "Cisco", "001678": "Cisco", "0016C8": "Cisco",
    "00175A": "Cisco", "001795": "Cisco", "0017DF": "Cisco",
    "0018B9": "Cisco", "001919": "Cisco", "001920": "Cisco",
    "001A2F": "Cisco", "001A70": "Cisco", "001A71": "Cisco",
    "001A71": "Cisco", "001AE2": "Cisco", "001B53": "Cisco",
    "001BD4": "Cisco", "001BD7": "Cisco", "001C57": "Cisco",
    "001C58": "Cisco", "001D45": "Cisco", "001D46": "Cisco",
    "001DE5": "Cisco", "001DE6": "Cisco", "001E13": "Cisco",
    "001E14": "Cisco", "001E49": "Cisco", "001E4A": "Cisco",
    "001E79": "Cisco",

    # Linksys / Belkin
    "000C41": "Linksys", "000E08": "Linksys", "000F66": "Linksys",
    "001217": "Linksys", "001310": "Linksys", "00141B": "Linksys",
    "001601": "Linksys", "001839": "Linksys", "001A70": "Linksys",
    "001C10": "Linksys", "001DF6": "Linksys", "001EE5": "Linksys",
    "00226B": "Linksys", "002369": "Linksys", "00259C": "Linksys",
    "002564": "Linksys",

    # Huawei
    "000FE2": "Huawei", "001E10": "Huawei", "002568": "Huawei",
    "0025E0": "Huawei", "0025F0": "Huawei", "002EC7": "Huawei",
    "00464B": "Huawei", "006EFF": "Huawei", "00E0FC": "Huawei",
    "041F0E": "Huawei", "043389": "Huawei", "04BD70": "Huawei",
    "04C06F": "Huawei", "04F938": "Huawei", "0819A6": "Huawei",
    "0C96BF": "Huawei", "0CD6BD": "Huawei", "109693": "Huawei",
    "10B1F8": "Huawei", "10C61F": "Huawei", "1495CE": "Huawei",
    "14B968": "Huawei", "14CF92": "Huawei", "184C65": "Huawei",
    "18C58A": "Huawei", "18DE0F": "Huawei", "200BC7": "Huawei",
    "203DB2": "Huawei", "2469A5": "Huawei", "2471F3": "Huawei",
    "248E11": "Huawei", "24BCF8": "Huawei", "2469A5": "Huawei",
    "28A6DB": "Huawei", "28BFBB": "Huawei", "2C55D3": "Huawei",
    "2CAB25": "Huawei", "30469A": "Huawei", "30D17E": "Huawei",
    "34CDBE": "Huawei", "381D5C": "Huawei", "38F889": "Huawei",
    "3C7843": "Huawei", "3C978E": "Huawei", "408815": "Huawei",
    "40CB A2": "Huawei", "44C346": "Huawei", "48435A": "Huawei",
    "484C68": "Huawei", "48AD08": "Huawei", "4C5499": "Huawei",
    "4C8BEF": "Huawei", "4CB16C": "Huawei", "500395": "Huawei",
    "502B73": "Huawei", "5054E8": "Huawei", "506F98": "Huawei",
    "54A51B": "Huawei", "58605F": "Huawei", "587F66": "Huawei",
    "5C4CA9": "Huawei", "5C7D5E": "Huawei", "5CB066": "Huawei",
    "6080B2": "Huawei", "60DE44": "Huawei", "60E701": "Huawei",
    "641007": "Huawei", "643673": "Huawei", "6466B3": "Huawei",
    "64A2F9": "Huawei", "683E34": "Huawei", "68856A": "Huawei",
    "688F84": "Huawei", "6C5940": "Huawei", "6CC1D2": "Huawei",
    "707990": "Huawei", "7072CF": "Huawei", "70723C": "Huawei",
    "708A09": "Huawei", "709F2D": "Huawei", "70A8E3": "Huawei",
    "74882A": "Huawei", "74A063": "Huawei", "78020F": "Huawei",
    "78D752": "Huawei", "7C110E": "Huawei", "7C601C": "Huawei",
    "7C608C": "Huawei", "807ABF": "Huawei", "80B686": "Huawei",
    "80D09B": "Huawei", "80FB06": "Huawei", "843DC6": "Huawei",
    "84A8E4": "Huawei", "880F10": "Huawei", "886ED6": "Huawei",
    "88A2D7": "Huawei", "88CEFA": "Huawei", "8C0D76": "Huawei",
    "8C34FD": "Huawei", "9001F9": "Huawei", "904E2B": "Huawei",
    "9017AC": "Huawei", "9060F1": "Huawei", "945BBE": "Huawei",
    "9885A2": "Huawei", "98E7F5": "Huawei", "9C28EF": "Huawei",
    "9C37F4": "Huawei", "9C741A": "Huawei",

    # LG Electronics
    "000FB4": "LG", "0014F6": "LG", "001C62": "LG",
    "001FE3": "LG", "0021FB": "LG", "002483": "LG",
    "0025E5": "LG", "0026E2": "LG", "00AA70": "LG",
    "08D42B": "LG", "10F96F": "LG", "1CBFCE": "LG",
    "204C9E": "LG", "28E02C": "LG", "2C54CF": "LG",
    "30766F": "LG", "305056": "LG", "341298": "LG",
    "3888EC": "LG", "3C2C99": "LG", "3C2EFF": "LG",
    "40B00A": "LG", "44B7D0": "LG", "50B7A3": "LG",
    "58A2B5": "LG", "5C4998": "LG", "64899A": "LG",
    "6C5C14": "LG", "78F882": "LG", "7C1C4E": "LG",
    "88C9D0": "LG", "8C3AE3": "LG", "A0B4A5": "LG",
    "A8B86E": "LG", "B4B5BE": "LG", "BC2E F6": "LG",
    "C0A3A2": "LG", "C449BB": "LG", "C4438F": "LG",
    "CC2D83": "LG", "D0D0FD": "LG", "E897F6": "LG",
    "E8F2E2": "LG", "F83077": "LG", "F895EA": "LG",
    "FC19D0": "LG", "FCD5D9": "LG",

    # Sony
    "000138": "Sony", "000444": "Sony", "000ADB": "Sony",
    "000E07": "Sony", "000FDE": "Sony", "0012EE": "Sony",
    "0013A9": "Sony", "00154E": "Sony", "001672": "Sony",
    "001792": "Sony", "0018F3": "Sony", "001A80": "Sony",
    "001D0D": "Sony", "001E39": "Sony", "001FA7": "Sony",
    "002128": "Sony", "00224D": "Sony", "0024BE": "Sony",
    "002567": "Sony", "002672": "Sony", "0027DD": "Sony",
    "00EB2D": "Sony", "28A183": "Sony", "2C648A": "Sony",
    "30A4DD": "Sony", "40B837": "Sony", "446D6C": "Sony",
    "546C0E": "Sony", "5CBA37": "Sony", "701CE7": "Sony",
    "78843C": "Sony", "78C2C0": "Sony", "8C8EF2": "Sony",
    "A0E453": "Sony", "B81899": "Sony", "BC6074": "Sony",
    "D86162": "Sony", "FC0FE6": "Sony",

    # Nintendo
    "002403": "Nintendo", "002659": "Nintendo", "0009BF": "Nintendo",
    "001656": "Nintendo", "001AE9": "Nintendo", "001CBE": "Nintendo",
    "001DBC": "Nintendo", "001E35": "Nintendo", "001F32": "Nintendo",
    "001FC5": "Nintendo", "002147": "Nintendo", "002219": "Nintendo",
    "0022D7": "Nintendo", "0022AA": "Nintendo", "002331": "Nintendo",
    "0024F3": "Nintendo", "002567": "Nintendo", "0025A0": "Nintendo",
    "002709": "Nintendo", "002F18": "Nintendo", "00EE07": "Nintendo",
    "00EE51": "Nintendo", "040CCE": "Nintendo", "0CBB8A": "Nintendo",
    "10A514": "Nintendo", "14F042": "Nintendo", "182A7B": "Nintendo",
    "205476": "Nintendo", "2C10C1": "Nintendo", "34AF2C": "Nintendo",
    "40D28A": "Nintendo", "582F40": "Nintendo", "58BDA3": "Nintendo",
    "606BFF": "Nintendo", "64B5C6": "Nintendo", "78A2A0": "Nintendo",
    "7CBB8A": "Nintendo", "8C56C5": "Nintendo", "8CCDE8": "Nintendo",
    "98B6E9": "Nintendo", "9CE635": "Nintendo", "A45C27": "Nintendo",
    "A4C0E1": "Nintendo", "B88AEC": "Nintendo", "B8AE6E": "Nintendo",
    "CC9E00": "Nintendo", "D86BF7": "Nintendo", "D8E087": "Nintendo",
    "E00C7F": "Nintendo", "E0E751": "Nintendo", "E84ECE": "Nintendo",
    "ECCF40": "Nintendo",

    # Roku
    "000921": "Roku", "0083FE": "Roku", "08D46A": "Roku",
    "10593D": "Roku", "2C4D54": "Roku", "2CF0A2": "Roku",
    "3C2ACA": "Roku", "504A6E": "Roku", "84EA64": "Roku",
    "B0A737": "Roku", "B0EE7B": "Roku", "C83A6B": "Roku",
    "CC6DA0": "Roku", "D02788": "Roku", "D4E227": "Roku",
    "D83134": "Roku", "DC3A5E": "Roku",

    # Sonos
    "000E58": "Sonos", "5CAAA6": "Sonos", "7828CA": "Sonos",
    "B8E937": "Sonos", "347E5C": "Sonos", "94DE80": "Sonos",
    "548CA0": "Sonos", "482136": "Sonos",

    # Raspberry Pi Foundation
    "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi",
    "DC4427": "Raspberry Pi", "E45F01": "Raspberry Pi",

    # Espressif (ESP32/ESP8266 IoT modules)
    "08F9E0": "Espressif", "10521C": "Espressif", "18FE34": "Espressif",
    "240AC4": "Espressif", "24B2DE": "Espressif", "2462AB": "Espressif",
    "2CF432": "Espressif", "30AEA4": "Espressif", "3C71BF": "Espressif",
    "4402FD": "Espressif", "4C11AE": "Espressif", "503CC4": "Espressif",
    "5CCF7F": "Espressif", "60019B": "Espressif", "68C63A": "Espressif",
    "7C9EBD": "Espressif", "807D3A": "Espressif", "840D8E": "Espressif",
    "8CAAB5": "Espressif", "94B97E": "Espressif", "98CDAC": "Espressif",
    "A020A6": "Espressif", "A4CF12": "Espressif", "AC67B2": "Espressif",
    "B4E62D": "Espressif", "BC:DD:C2": "Espressif", "C44F33": "Espressif",
    "CC50E3": "Espressif", "D8BFC0": "Espressif", "DC4F22": "Espressif",
    "E09806": "Espressif", "E0983D": "Espressif", "E8DB84": "Espressif",
    "F4CFA2": "Espressif", "FC4E36": "Espressif",

    # Ubiquiti
    "00156D": "Ubiquiti", "0418D6": "Ubiquiti", "18E829": "Ubiquiti",
    "245A4C": "Ubiquiti", "247B0D": "Ubiquiti", "2C24B2": "Ubiquiti",
    "347A60": "Ubiquiti", "44D9E7": "Ubiquiti", "683A1E": "Ubiquiti",
    "74ACB9": "Ubiquiti", "784558": "Ubiquiti", "788A20": "Ubiquiti",
    "802AA8": "Ubiquiti", "9CFCF0": "Ubiquiti", "B4FBE4": "Ubiquiti",
    "D021F9": "Ubiquiti", "E063DA": "Ubiquiti", "F492BF": "Ubiquiti",
    "FC16EC": "Ubiquiti", "FCECDA": "Ubiquiti",

    # D-Link
    "001195": "D-Link", "0015E9": "D-Link", "001B11": "D-Link",
    "001CB0": "D-Link", "001CF0": "D-Link", "001E58": "D-Link",
    "002191": "D-Link", "00222D": "D-Link", "0024A5": "D-Link",
    "002552": "D-Link", "002680": "D-Link", "00265A": "D-Link",
    "00179A": "D-Link", "000D88": "D-Link", "000F3D": "D-Link",
    "0011F5": "D-Link", "001346": "D-Link", "001495": "D-Link",
    "0017E8": "D-Link", "001921": "D-Link", "1C7EE5": "D-Link",
    "1CAFF7": "D-Link", "28107B": "D-Link", "30B5C2": "D-Link",
    "340804": "D-Link", "3C1E04": "D-Link", "5CE30E": "D-Link",
    "78542E": "D-Link", "7C452D": "D-Link", "84C9B2": "D-Link",
    "9094E4": "D-Link", "908D78": "D-Link", "98DAC4": "D-Link",
    "ACF1DF": "D-Link", "B8A386": "D-Link", "BC5FF4": "D-Link",
    "BC8893": "D-Link", "C8BE19": "D-Link", "C8D3A3": "D-Link",
    "CCB255": "D-Link", "F07D68": "D-Link", "F0B429": "D-Link",
    "F44B2A": "D-Link",

    # Motorola / Lenovo
    "000423": "Motorola", "0014F1": "Motorola", "000CE5": "Motorola",
    "001247": "Motorola", "001ADE": "Motorola", "001EAE": "Motorola",
    "002335": "Motorola", "001CBF": "Motorola", "1801F1": "Motorola",
    "24DA9B": "Motorola", "283737": "Motorola", "40886A": "Motorola",
    "44802D": "Motorola", "5C5A1D": "Motorola", "6C5A34": "Motorola",
    "6CB4A7": "Motorola", "74B57E": "Motorola", "88797E": "Motorola",
    "C4437F": "Motorola", "D4E880": "Motorola", "E4907E": "Motorola",
    "F4F524": "Motorola",

    # Lenovo
    "001E4C": "Lenovo", "002170": "Lenovo", "0026B9": "Lenovo",
    "34E12D": "Lenovo", "48E244": "Lenovo", "504061": "Lenovo",
    "545AA6": "Lenovo", "54EE75": "Lenovo", "6C0B84": "Lenovo",
    "74E543": "Lenovo", "70F166": "Lenovo", "7C67A2": "Lenovo",
    "8CEC4B": "Lenovo", "7C334C": "Lenovo", "7876D7": "Lenovo",
    "98FAE3": "Lenovo", "B04F13": "Lenovo", "C0D984": "Lenovo",
    "D0579A": "Lenovo", "D4619D": "Lenovo", "E8D0FC": "Lenovo",
    "F82F08": "Lenovo", "FC4596": "Lenovo",

    # Aruba / HPE
    "000B86": "Aruba Networks", "001A1E": "Aruba Networks",
    "04BD88": "Aruba Networks", "24DEA7": "Aruba Networks",
    "400E85": "Aruba Networks", "6CF37F": "Aruba Networks",
    "70B317": "Aruba Networks", "8C2DAA": "Aruba Networks",
    "947BDC": "Aruba Networks", "9C1C12": "Aruba Networks",
    "ACB327": "Aruba Networks", "B45D50": "Aruba Networks",
    "D8C7C8": "Aruba Networks",

    # Qualcomm / Atheros
    "00037F": "Atheros", "000AAD": "Atheros", "001374": "Atheros",
    "001CCD": "Atheros", "0023F8": "Atheros", "002689": "Atheros",
    "981E15": "Qualcomm", "38BC01": "Qualcomm", "50C2E8": "Qualcomm",

    # Broadcom
    "00104B": "Broadcom", "001018": "Broadcom", "000AF5": "Broadcom",
    "0010EE": "Broadcom", "001250": "Broadcom",

    # Realtek
    "001096": "Realtek", "000A80": "Realtek", "000CE7": "Realtek",
    "001264": "Realtek", "00E04C": "Realtek", "B82F08": "Realtek",
    "C83A35": "Realtek", "D8EB46": "Realtek", "70B14E": "Realtek",
    "48022A": "Realtek", "52540F": "Realtek",

    # MediaTek
    "001176": "MediaTek", "00168D": "MediaTek", "000CE7": "MediaTek",

    # OnePlus
    "94652D": "OnePlus", "C0EE40": "OnePlus",

    # Google Nest
    "18B430": "Google Nest", "1C3E84": "Google Nest",
    "2053CA": "Google Nest", "48D6D5": "Google Nest",
    "6C5AB0": "Google Nest", "A4770B": "Google Nest",
    "CCFB65": "Google Nest", "E8F2E2": "Google Nest",
    "F47FB7": "Google Nest", "FCADB0": "Google Nest",

    # Ring (Amazon)
    "5C4813": "Ring", "74EC1C": "Ring", "D4F98D": "Ring",

    # Wyze
    "2CAA8E": "Wyze",

    # Philips Hue
    "001788": "Philips Hue", "ECB5FA": "Philips Hue",

    # Generic / Other common
    "FFFFFFFFFFFFFF": "Broadcast",
}


class OUIDatabase:
    """
    Offline OUI (Organizationally Unique Identifier) database
    for resolving MAC address prefixes to vendor names.
    """

    def __init__(self):
        self._db = {}
        self._load()

    def _load(self):
        """Load the embedded OUI database."""
        for prefix, vendor in OUI_DATABASE.items():
            # Normalize: remove colons/hyphens/spaces and uppercase
            clean = prefix.replace(":", "").replace("-", "").replace(" ", "").upper()
            if len(clean) >= 6:
                self._db[clean[:6]] = vendor

        logger.info(f"OUI database loaded: {len(self._db)} vendor prefixes.")

    def lookup(self, mac_address: str) -> str:
        """
        Look up the vendor name for a MAC address.

        Args:
            mac_address: MAC address in any common format
                         (e.g., "AA:BB:CC:DD:EE:FF", "AA-BB-CC-DD-EE-FF", "AABBCCDDEEFF")

        Returns:
            Vendor name string, or "Unknown" if not found.
        """
        if not mac_address:
            return "Unknown"

        # Normalize MAC: remove separators, uppercase
        clean = mac_address.replace(":", "").replace("-", "").replace(".", "").replace(" ", "").upper()

        if len(clean) < 6:
            return "Unknown"

        prefix = clean[:6]

        # Try exact 6-char (MA-L) match first
        vendor = self._db.get(prefix)
        if vendor:
            return vendor

        # Try 7-char (MA-M) and 9-char (MA-S) matches
        for length in [7, 9]:
            if len(clean) >= length:
                longer_prefix = clean[:length]
                vendor = self._db.get(longer_prefix)
                if vendor:
                    return vendor

        return "Unknown"

    def get_prefix(self, mac_address: str) -> str:
        """Extract the OUI prefix (first 3 bytes) from a MAC address."""
        clean = mac_address.replace(":", "").replace("-", "").replace(".", "").replace(" ", "").upper()
        if len(clean) >= 6:
            return clean[:6]
        return ""

    @property
    def vendor_count(self) -> int:
        """Return the number of vendor prefixes in the database."""
        return len(self._db)
