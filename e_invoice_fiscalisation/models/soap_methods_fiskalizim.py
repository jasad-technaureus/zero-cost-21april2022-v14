import base64
import hashlib

import requests
import signxml
from OpenSSL import crypto
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from lxml import etree
from signxml import XMLSigner, XMLVerifier
import re


FISCALIZATION_SCHEMA = "https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema"
EINVOICE_SCHEMA = "https://Einvoice.tatime.gov.al/EinvoiceService/schema"
VERSION = "3"


def get_header_data(datetime, uuid):
    header_data = {
        '1__SendDateTime': datetime,
        '2__UUID': uuid
    }
    return header_data


def get_request_data():
    request_data = {
            '1__xmlns': FISCALIZATION_SCHEMA,
            '2__xmlns:ns2': "http://www.w3.org/2000/09/xmldsig#",
            '3__Id': 'Request',
            '4__Version': VERSION
        }

    return request_data

def get_einvoice_data():
    request_data = {
            '1__xmlns': EINVOICE_SCHEMA,
            '2__Id': 'Request',
            '3__Version': "1"
        }

    return request_data

def _dict_sort_key(key_value):
    key = key_value[0]
    match = re.match('(\d+)__.*', key)
    return match and int(match.groups()[0]) or key

def _remove_order_id(key):
    match = re.match('\d+__(.*)', key)
    return match and match.groups()[0] or key


def dict2xml(d, root_node=None):
    wrap = False if root_node is None or isinstance(d, list) else True
    root = 'objects' if root_node is None else root_node
    root_singular = root[:-1] if 's' == root[-1] and root_node is None else root
    xml = ''
    children = []
    end_tag_element = False

    if isinstance(d, dict):
        d_sorted = sorted(d.items(), key=(lambda key_value: _dict_sort_key(key_value)))
        for key, value in d_sorted:
            key2 = _remove_order_id(key)
            end_tag_element = False
            if isinstance(value, dict):
                children.append(dict2xml(value, key))
            elif isinstance(value, list):
                children.append(dict2xml(value, key))
            else:
                if '@' not in key:
                    xml = xml + ' ' + key2 + '="' + str(value) + '"'
                else:
                    xml = xml + '>' + str(value) + '</' + key2[1:]
                    end_tag_element = True
    else:
        for value in d:
            children.append(dict2xml(value, root_singular))

    end_tag = '>' if 0 < len(children) or end_tag_element else '/>'

    if wrap or isinstance(d, dict):
        xml = '<' + _remove_order_id(root) + xml + end_tag

    if 0 < len(children):
        for child in children:
            xml = xml + child

        if wrap or isinstance(d, dict):
            xml = xml + '</' + _remove_order_id(root) + '>'

    return xml


def make_request(xml_data, url, ubl=False, proxy_var=False):
    if not ubl:
        request_data = """<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema">
           <SOAP-ENV:Header/>
           <ns0:Body>
              {}
           </ns0:Body>
        </SOAP-ENV:Envelope>""".format(xml_data)
    else:
        request_data = """<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
                   <S:Header/>
                   <S:Body>
                      {}
                   </S:Body>
                </S:Envelope>""".format(xml_data)

    headers = {"Content-Type": "text/xml; charset=UTF-8", "Content-Length": str(len(request_data))}

    proxies = False
    if proxy_var:
        proxies = {'https': proxy_var}

    print('REQUEST_DATA', request_data)
    # request_attachment = self.env['ir.attachment'].create({
    #     'name': self.name + '_ubl_xml_file.xml',
    #     'datas': base64.encodebytes(str(decoded_ubl).encode(encoding="utf-8")),
    #     'mimetype': 'application/xml',
    # })
    # self.signed_ubl_xml_file = request_attachment

    response = requests.post(url=url, headers=headers, data=request_data, verify=False, proxies=proxies)

    return response


#Kthen numrin IIC qe sherben si numer identifikues per kerkesen qe dergohet per regjistrimin e faturave
def get_IIC(iic_input, certificate, password):
    p12 = crypto.load_pkcs12(base64.b64decode(certificate), bytes(password, 'utf-8'))
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
    private_key = serialization.load_pem_private_key(
        private_key,
        password=None,
        backend=default_backend()
    )
    #Create IIC signature according to RSASSA-PKCS-v1_5
    signature = private_key.sign(iic_input.encode('ascii'), padding.PKCS1v15(), hashes.SHA256())
    #Hash IIC signature with MD5 to create IIC
    iic = hashlib.md5(signature)
    signature = signature.hex()
    #Convert IIC to hexadecimal
    iic = iic.hexdigest().upper()
    return signature, iic


#Funksioni qe merr si parameter kerkesen xml, ben nenshkrimin elektronik dhe kthen xml e nenshkruar
def sign_XML(request_to_sign, certificate, password):
#base64.b64decode(certificate)
    root = etree.fromstring(request_to_sign)
    p12 = crypto.load_pkcs12(base64.b64decode(certificate), bytes(password, 'utf-8'))
    cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())

    signed_root = XMLSigner(method=signxml.methods.enveloped, signature_algorithm='rsa-sha256', digest_algorithm='sha256', c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#').sign(root, key=private_key, cert=cert,  id_attribute='Request')

    #signature = XMLVerifier().verify(signed_root, x509_cert=cert).signature_xml

    signed_root_str = etree.tostring(signed_root).decode('utf-8')
    # print('signed_root_str', signed_root_str)
    return signed_root_str


def register_Request(url, certificate_file, password, dict_data, request_type, ubl=False, proxy_var=False):

    xml_data = dict2xml(dict_data, request_type)

    xml_signed = sign_XML(xml_data, certificate_file, password)
    # print('xml_signed', xml_signed)
    response = make_request(xml_signed, url, ubl=ubl, proxy_var=proxy_var)

    # if response.status_code == 404:
    #     return -1

    xml_response = etree.fromstring(response.content)

    return xml_response


def get_xml_signed(certificate, password, dict_data, request_type):

    xml_data = dict2xml(dict_data, request_type)
    xml_signed = sign_XML(xml_data, certificate, password)
    return xml_signed


# def sign_UBL(certificate, password, root, ns):
#
#     extensions = etree.Element(ns['ext'] + 'UBLExtensions')
#     extension = etree.SubElement(extensions, ns['ext'] + 'UBLExtension')
#     extension_content = etree.SubElement(extension, ns['ext'] + 'ExtensionContent')
#     ubl_doc_signature = etree.SubElement(extension_content, ns['sig'] + 'UBLDocumentSignatures')
#     sign_info = etree.SubElement(ubl_doc_signature, ns['sac'] + 'SignatureInformation')
#     sign_info.text=''
#     root.insert(0,extensions)
#
#     p12 = crypto.load_pkcs12(base64.b64decode(certificate), bytes(password, 'utf-8'))
#     cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
#     private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
#
#     signed_root = XMLSigner(method=signxml.methods.enveloped, signature_algorithm='rsa-sha256', digest_algorithm='sha256', c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#').sign(root, key=private_key, cert=cert,  id_attribute='Request')
#
#
#     signature = XMLVerifier().verify(signed_root, x509_cert=cert).signature_xml
#
#     sign_info.insert(1,signature)
#
#     return root
