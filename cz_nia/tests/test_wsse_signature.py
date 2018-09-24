"""Unittests for wsse.signature module."""
import os
from unittest import TestCase

from lxml.etree import QName
from zeep import ns
from zeep.exceptions import SignatureVerificationFailed
from zeep.wsse.signature import _make_sign_key

from cz_nia.tests.utils import load_xml
from cz_nia.wsse import BinarySignature, MemorySignature, SAMLTokenSignature, Signature
from cz_nia.wsse.signature import _signature_prepare

CERT_FILE = os.path.join(os.path.dirname(__file__), 'certificate.pem')
KEY_FILE = os.path.join(os.path.dirname(__file__), 'key.pem')
ENVELOPE = """
    <soapenv:Envelope xmlns:tns="http://tests.python-zeep.org/" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
        <soapenv:Header></soapenv:Header>
        <soapenv:Body>
            <tns:Function>
                <tns:Argument>OK</tns:Argument>
            </tns:Function>
        </soapenv:Body>
    </soapenv:Envelope>
    """


class TestSignaturePrepare(TestCase):
    """Unittests for _signature_prepare."""

    def setUp(self):
        with open(KEY_FILE) as key, open(CERT_FILE) as cert:
            self.key = _make_sign_key(key.read(), cert.read(), None)

    def test_newline_strip(self):
        security, _, _ = _signature_prepare(load_xml(ENVELOPE), self.key)
        signature = security.find(QName(ns.DS, 'Signature'))
        for element in signature.iter():
            if element.tag in ('{http://www.w3.org/2000/09/xmldsig#}SignatureValue',
                               '{http://www.w3.org/2000/09/xmldsig#}X509IssuerSerial',
                               '{http://www.w3.org/2000/09/xmldsig#}X509IssuerName',
                               '{http://www.w3.org/2000/09/xmldsig#}X509SerialNumber',
                               '{http://www.w3.org/2000/09/xmldsig#}X509Certificate'):
                # These are placed after the stripping, so we do not check them
                continue
            if element.text is not None:
                self.assertNotIn('\n', element.text)
            if element.tail is not None:
                self.assertNotIn('\n', element.tail)


class TestBinarySignature(TestCase):
    """Unittests for BinarySignature."""

    def test_signature_binary(self):
        plugin = BinarySignature(KEY_FILE, CERT_FILE)
        envelope, headers = plugin.apply(load_xml(ENVELOPE), {})
        plugin.verify(envelope)
        # Test that the reference is correct
        bintok = envelope.xpath('soapenv:Header/wsse:Security/wsse:BinarySecurityToken',
                                namespaces={'soapenv': ns.SOAP_ENV_11, 'wsse': ns.WSSE})[0]
        ref = envelope.xpath('soapenv:Header/wsse:Security/ds:Signature/ds:KeyInfo/wsse:SecurityTokenReference'
                             '/wsse:Reference',
                             namespaces={'soapenv': ns.SOAP_ENV_11, 'wsse': ns.WSSE, 'ds': ns.DS})[0]
        self.assertEqual('#' + bintok.attrib[QName(ns.WSU, 'Id')], ref.attrib['URI'])


class TestMemorySignature(TestCase):
    """Unittests for MemorySignature."""

    def test_signature(self):
        with open(KEY_FILE) as key, open(CERT_FILE) as cert:
            plugin = MemorySignature(key.read(), cert.read())
        envelope, headers = plugin.apply(load_xml(ENVELOPE), {})
        plugin.verify(envelope)

    def test_verify_no_header(self):
        plugin = MemorySignature(open(KEY_FILE).read(), open(CERT_FILE).read())
        with self.assertRaises(SignatureVerificationFailed):
            plugin.verify(load_xml(
                """
                <soapenv:Envelope xmlns:tns="http://tests.python-zeep.org/"
                xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
                xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
                    <soapenv:Body>
                        <tns:Function>
                            <tns:Argument>OK</tns:Argument>
                        </tns:Function>
                    </soapenv:Body>
                </soapenv:Envelope>
                """))

    def test_verify_no_security(self):
        plugin = MemorySignature(open(KEY_FILE).read(), open(CERT_FILE).read())
        with self.assertRaises(SignatureVerificationFailed):
            plugin.verify(load_xml(ENVELOPE))

    def test_verify_no_signature(self):
        plugin = MemorySignature(open(KEY_FILE).read(), open(CERT_FILE).read())
        plugin.verify(load_xml(
            """
            <soapenv:Envelope xmlns:tns="http://tests.python-zeep.org/" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
            xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
            xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
                <soapenv:Header>
                    <wsse:Security
                    xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
                    </wsse:Security>
                </soapenv:Header>
                <soapenv:Body>
                    <tns:Function>
                        <tns:Argument>OK</tns:Argument>
                    </tns:Function>
                </soapenv:Body>
            </soapenv:Envelope>
            """))


class TestSignature(TestCase):
    """Unittests for Signature."""

    def test_signature(self):
        plugin = Signature(KEY_FILE, CERT_FILE)
        envelope, headers = plugin.apply(load_xml(ENVELOPE), {})
        plugin.verify(envelope)


class TestSAMLTokenSignature(TestCase):
    """Unittests dof SAMLTokenSignature."""

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'assertion.xml')) as f:
            self.assertion = load_xml(f.read())

    def test_signature_saml(self):
        plugin = SAMLTokenSignature(self.assertion)
        envelope, headers = plugin.apply(load_xml(ENVELOPE), {})
        plugin.verify(envelope)
