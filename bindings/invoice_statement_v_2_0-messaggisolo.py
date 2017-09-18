# /home/sergio/buildout/parts/e-account/account_invoice_declaration/bindings/invoice_declaration_v_2_0.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:46b5c76ddf538b5ba38ed9e41b139df8cafd8cf5
# Generated 2017-08-05 18:18:58.388680 by PyXB version 1.2.4 using Python 2.7.12.final.0
# Namespace http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0

from __future__ import unicode_literals
import logging
import io
import sys
_logger = logging.getLogger(__name__)
try:
    import pyxb
    import pyxb.binding
    import pyxb.binding.saxer
    import pyxb.utils.utility
    import pyxb.utils.domutils
    import pyxb.utils.six as _six
    # Import bindings for namespaces imported into schema
    import pyxb.binding.datatypes
except ImportError as err:
    _logger.debug(err)

# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:bfbbe556-79f9-11e7-afb3-b05adae3c683')

# Version of PyXB used to generate the bindings
_PyXBVersion = '1.2.4'
# Generated bindings are not compatible across PyXB versions
if pyxb.__version__ != _PyXBVersion:
    raise pyxb.PyXBVersionError(_PyXBVersion)

# Import bindings for namespaces imported into schema
# import _ds as _ImportedBinding__ds
from openerp.addons.l10n_it_fatturapa.bindings import _ds as _ImportedBinding__ds

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.NamespaceForURI('http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0', create_if_missing=True)
Namespace.configureCategories(['typeBinding', 'elementBinding'])
_Namespace_ds = _ImportedBinding__ds.Namespace
_Namespace_ds.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text, default_namespace=None, location_base=None):
    """Parse the given XML and use the document element to create a
    Python instance.

    @param xml_text An XML document.  This should be data (Python 2
    str or Python 3 bytes), or a text (Python 2 unicode or Python 3
    str) in the L{pyxb._InputEncoding} encoding.

    @keyword default_namespace The L{pyxb.Namespace} instance to use as the
    default namespace where there is no default namespace in scope.
    If unspecified or C{None}, the namespace of the module containing
    this function will be used.

    @keyword location_base: An object to be recorded as the base of all
    L{pyxb.utils.utility.Location} instances associated with events and
    objects handled by the parser.  You might pass the URI from which
    the document was obtained.
    """

    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement, default_namespace=default_namespace)
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=default_namespace, location_base=location_base)
    handler = saxer.getContentHandler()
    xmld = xml_text
    if isinstance(xmld, _six.text_type):
        xmld = xmld.encode(pyxb._InputEncoding)
    saxer.parse(io.BytesIO(xmld))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, default_namespace)


# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}TipoFile_Type
class TipoFile_Type (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'TipoFile_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 47, 2)
    _Documentation = None
TipoFile_Type._InitializeFacetMap()
Namespace.addCategoryObject('typeBinding', 'TipoFile_Type', TipoFile_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}Esito_Type
class Esito_Type (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'Esito_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 55, 2)
    _Documentation = None
Esito_Type._CF_length = pyxb.binding.facets.CF_length(value=pyxb.binding.datatypes.nonNegativeInteger(4))
Esito_Type._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=Esito_Type, enum_prefix=None)
Esito_Type.ES01 = Esito_Type._CF_enumeration.addEnumeration(unicode_value='ES01', tag='ES01')
Esito_Type.ES02 = Esito_Type._CF_enumeration.addEnumeration(unicode_value='ES02', tag='ES02')
Esito_Type.ES03 = Esito_Type._CF_enumeration.addEnumeration(unicode_value='ES03', tag='ES03')
Esito_Type._InitializeFacetMap(Esito_Type._CF_length,
   Esito_Type._CF_enumeration)
Namespace.addCategoryObject('typeBinding', 'Esito_Type', Esito_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}MessageId_Type
class MessageId_Type (pyxb.binding.datatypes.normalizedString):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'MessageId_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 89, 2)
    _Documentation = None
MessageId_Type._CF_maxLength = pyxb.binding.facets.CF_maxLength(value=pyxb.binding.datatypes.nonNegativeInteger(300))
MessageId_Type._InitializeFacetMap(MessageId_Type._CF_maxLength)
Namespace.addCategoryObject('typeBinding', 'MessageId_Type', MessageId_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}IDFile_Type
class IDFile_Type (pyxb.binding.datatypes.normalizedString):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'IDFile_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 96, 2)
    _Documentation = None
IDFile_Type._CF_pattern = pyxb.binding.facets.CF_pattern()
IDFile_Type._CF_pattern.addPattern(pattern='(\\p{IsBasicLatin}{1,18})')
IDFile_Type._InitializeFacetMap(IDFile_Type._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'IDFile_Type', IDFile_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}CodiceErrore_Type
class CodiceErrore_Type (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'CodiceErrore_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 103, 2)
    _Documentation = None
CodiceErrore_Type._CF_length = pyxb.binding.facets.CF_length(value=pyxb.binding.datatypes.nonNegativeInteger(5))
CodiceErrore_Type._InitializeFacetMap(CodiceErrore_Type._CF_length)
Namespace.addCategoryObject('typeBinding', 'CodiceErrore_Type', CodiceErrore_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}NomeFile_Type
class NomeFile_Type (pyxb.binding.datatypes.normalizedString):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'NomeFile_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 109, 2)
    _Documentation = None
NomeFile_Type._CF_pattern = pyxb.binding.facets.CF_pattern()
NomeFile_Type._CF_pattern.addPattern(pattern='[a-zA-Z0-9_\\.]{9,50}')
NomeFile_Type._InitializeFacetMap(NomeFile_Type._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'NomeFile_Type', NomeFile_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}String255Latin_Type
class String255Latin_Type (pyxb.binding.datatypes.normalizedString):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'String255Latin_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 115, 2)
    _Documentation = None
String255Latin_Type._CF_pattern = pyxb.binding.facets.CF_pattern()
String255Latin_Type._CF_pattern.addPattern(pattern='[\\p{IsBasicLatin}\\p{IsLatin-1Supplement}]{1,255}')
String255Latin_Type._InitializeFacetMap(String255Latin_Type._CF_pattern)
Namespace.addCategoryObject('typeBinding', 'String255Latin_Type', String255Latin_Type)

# Atomic simple type: {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}Versione_Type
class Versione_Type (pyxb.binding.datatypes.string):

    """An atomic simple type."""

    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'Versione_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 121, 2)
    _Documentation = None
Versione_Type._CF_maxLength = pyxb.binding.facets.CF_maxLength(value=pyxb.binding.datatypes.nonNegativeInteger(5))
Versione_Type._InitializeFacetMap(Versione_Type._CF_maxLength)
Namespace.addCategoryObject('typeBinding', 'Versione_Type', Versione_Type)

# Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}RifArchivio_Type with content type ELEMENT_ONLY
class RifArchivio_Type (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}RifArchivio_Type with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'RifArchivio_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 40, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element IDArchivio uses Python identifier IDArchivio
    __IDArchivio = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'IDArchivio'), 'IDArchivio', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_RifArchivio_Type_IDArchivio', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 42, 6), )

    
    IDArchivio = property(__IDArchivio.value, __IDArchivio.set, None, None)

    
    # Element NomeArchivio uses Python identifier NomeArchivio
    __NomeArchivio = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'NomeArchivio'), 'NomeArchivio', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_RifArchivio_Type_NomeArchivio', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 43, 6), )

    
    NomeArchivio = property(__NomeArchivio.value, __NomeArchivio.set, None, None)

    _ElementMap.update({
        __IDArchivio.name() : __IDArchivio,
        __NomeArchivio.name() : __NomeArchivio
    })
    _AttributeMap.update({
        
    })
Namespace.addCategoryObject('typeBinding', 'RifArchivio_Type', RifArchivio_Type)


# Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}ListaErrori_Type with content type ELEMENT_ONLY
class ListaErrori_Type (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}ListaErrori_Type with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'ListaErrori_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 76, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element Errore uses Python identifier Errore
    __Errore = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'Errore'), 'Errore', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_ListaErrori_Type_Errore', True, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 78, 6), )

    
    Errore = property(__Errore.value, __Errore.set, None, None)

    _ElementMap.update({
        __Errore.name() : __Errore
    })
    _AttributeMap.update({
        
    })
Namespace.addCategoryObject('typeBinding', 'ListaErrori_Type', ListaErrori_Type)


# Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}Errore_Type with content type ELEMENT_ONLY
class Errore_Type (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}Errore_Type with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'Errore_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 82, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element Codice uses Python identifier Codice
    __Codice = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'Codice'), 'Codice', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_Errore_Type_Codice', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 84, 6), )

    
    Codice = property(__Codice.value, __Codice.set, None, None)

    
    # Element Descrizione uses Python identifier Descrizione
    __Descrizione = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'Descrizione'), 'Descrizione', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_Errore_Type_Descrizione', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 85, 6), )

    
    Descrizione = property(__Descrizione.value, __Descrizione.set, None, None)

    _ElementMap.update({
        __Codice.name() : __Codice,
        __Descrizione.name() : __Descrizione
    })
    _AttributeMap.update({
        
    })
Namespace.addCategoryObject('typeBinding', 'Errore_Type', Errore_Type)


# Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}EsitoFile_Type with content type ELEMENT_ONLY
class EsitoFile_Type (pyxb.binding.basis.complexTypeDefinition):
    """Complex type {http://ivaservizi.agenziaentrate.gov.it/docs/xsd/file/v2.0}EsitoFile_Type with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, 'EsitoFile_Type')
    _XSDLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 23, 2)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element TipoFile uses Python identifier TipoFile
    __TipoFile = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'TipoFile'), 'TipoFile', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_TipoFile', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 25, 6), )

    
    TipoFile = property(__TipoFile.value, __TipoFile.set, None, None)

    
    # Element IDFile uses Python identifier IDFile
    __IDFile = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'IDFile'), 'IDFile', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_IDFile', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 26, 6), )

    
    IDFile = property(__IDFile.value, __IDFile.set, None, None)

    
    # Element NomeFile uses Python identifier NomeFile
    __NomeFile = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'NomeFile'), 'NomeFile', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_NomeFile', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 27, 6), )

    
    NomeFile = property(__NomeFile.value, __NomeFile.set, None, None)

    
    # Element DataOraRicezione uses Python identifier DataOraRicezione
    __DataOraRicezione = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'DataOraRicezione'), 'DataOraRicezione', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_DataOraRicezione', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 28, 6), )

    
    DataOraRicezione = property(__DataOraRicezione.value, __DataOraRicezione.set, None, None)

    
    # Element RifArchivio uses Python identifier RifArchivio
    __RifArchivio = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'RifArchivio'), 'RifArchivio', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_RifArchivio', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 29, 6), )

    
    RifArchivio = property(__RifArchivio.value, __RifArchivio.set, None, None)

    
    # Element Esito uses Python identifier Esito
    __Esito = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'Esito'), 'Esito', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_Esito', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 30, 6), )

    
    Esito = property(__Esito.value, __Esito.set, None, None)

    
    # Element ListaErrori uses Python identifier ListaErrori
    __ListaErrori = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'ListaErrori'), 'ListaErrori', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_ListaErrori', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 31, 6), )

    
    ListaErrori = property(__ListaErrori.value, __ListaErrori.set, None, None)

    
    # Element MessageID uses Python identifier MessageID
    __MessageID = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'MessageID'), 'MessageID', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_MessageID', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 32, 6), )

    
    MessageID = property(__MessageID.value, __MessageID.set, None, None)

    
    # Element PECMessageID uses Python identifier PECMessageID
    __PECMessageID = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'PECMessageID'), 'PECMessageID', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_PECMessageID', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 33, 6), )

    
    PECMessageID = property(__PECMessageID.value, __PECMessageID.set, None, None)

    
    # Element Note uses Python identifier Note
    __Note = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'Note'), 'Note', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_Note', False, pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 34, 6), )

    
    Note = property(__Note.value, __Note.set, None, None)

    
    # Element {http://www.w3.org/2000/09/xmldsig#}Signature uses Python identifier Signature
    __Signature = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(_Namespace_ds, 'Signature'), 'Signature', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_httpwww_w3_org200009xmldsigSignature', False, pyxb.utils.utility.Location('http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd', 43, 0), )

    
    Signature = property(__Signature.value, __Signature.set, None, None)

    
    # Attribute versione uses Python identifier versione
    __versione = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, 'versione'), 'versione', '__httpivaservizi_agenziaentrate_gov_itdocsxsdfilev2_0_EsitoFile_Type_versione', Versione_Type, fixed=True, unicode_default='2.0', required=True)
    __versione._DeclarationLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 37, 4)
    __versione._UseLocation = pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 37, 4)
    
    versione = property(__versione.value, __versione.set, None, None)

    _ElementMap.update({
        __TipoFile.name() : __TipoFile,
        __IDFile.name() : __IDFile,
        __NomeFile.name() : __NomeFile,
        __DataOraRicezione.name() : __DataOraRicezione,
        __RifArchivio.name() : __RifArchivio,
        __Esito.name() : __Esito,
        __ListaErrori.name() : __ListaErrori,
        __MessageID.name() : __MessageID,
        __PECMessageID.name() : __PECMessageID,
        __Note.name() : __Note,
        __Signature.name() : __Signature
    })
    _AttributeMap.update({
        __versione.name() : __versione
    })
Namespace.addCategoryObject('typeBinding', 'EsitoFile_Type', EsitoFile_Type)


EsitoFile = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'EsitoFile'), EsitoFile_Type, documentation='Esito file', location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 14, 2))
Namespace.addCategoryObject('elementBinding', EsitoFile.name().localName(), EsitoFile)



RifArchivio_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'IDArchivio'), IDFile_Type, scope=RifArchivio_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 42, 6)))

RifArchivio_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'NomeArchivio'), NomeFile_Type, scope=RifArchivio_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 43, 6)))

def _BuildAutomaton ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(RifArchivio_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'IDArchivio')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 42, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(RifArchivio_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'NomeArchivio')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 43, 6))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
RifArchivio_Type._Automaton = _BuildAutomaton()




ListaErrori_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'Errore'), Errore_Type, scope=ListaErrori_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 78, 6)))

def _BuildAutomaton_ ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_
    del _BuildAutomaton_
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(ListaErrori_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'Errore')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 78, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    transitions = []
    transitions.append(fac.Transition(st_0, [
         ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
ListaErrori_Type._Automaton = _BuildAutomaton_()




Errore_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'Codice'), CodiceErrore_Type, scope=Errore_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 84, 6)))

Errore_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'Descrizione'), String255Latin_Type, scope=Errore_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 85, 6)))

def _BuildAutomaton_2 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_2
    del _BuildAutomaton_2
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(Errore_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'Codice')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 84, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(Errore_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'Descrizione')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 85, 6))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    st_1._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
Errore_Type._Automaton = _BuildAutomaton_2()




EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'TipoFile'), TipoFile_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 25, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'IDFile'), IDFile_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 26, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'NomeFile'), NomeFile_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 27, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'DataOraRicezione'), pyxb.binding.datatypes.dateTime, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 28, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'RifArchivio'), RifArchivio_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 29, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'Esito'), Esito_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 30, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'ListaErrori'), ListaErrori_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 31, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'MessageID'), MessageId_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 32, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'PECMessageID'), MessageId_Type, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 33, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'Note'), pyxb.binding.datatypes.string, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 34, 6)))

EsitoFile_Type._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(_Namespace_ds, 'Signature'), _ImportedBinding__ds.SignatureType, scope=EsitoFile_Type, location=pyxb.utils.utility.Location('http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd', 43, 0)))

def _BuildAutomaton_3 ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_3
    del _BuildAutomaton_3
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 29, 6))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 31, 6))
    counters.add(cc_1)
    cc_2 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 33, 6))
    counters.add(cc_2)
    cc_3 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 34, 6))
    counters.add(cc_3)
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'TipoFile')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 25, 6))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'IDFile')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 26, 6))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'NomeFile')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 27, 6))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'DataOraRicezione')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 28, 6))
    st_3 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'RifArchivio')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 29, 6))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'Esito')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 30, 6))
    st_5 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_5)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'ListaErrori')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 31, 6))
    st_6 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_6)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'MessageID')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 32, 6))
    st_7 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_7)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'PECMessageID')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 33, 6))
    st_8 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_8)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(None, 'Note')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 34, 6))
    st_9 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_9)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(EsitoFile_Type._UseForTag(pyxb.namespace.ExpandedName(_Namespace_ds, 'Signature')), pyxb.utils.utility.Location('../common/main/DatiFatturaMessaggiv2.0.xsd', 35, 6))
    st_10 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_10)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
         ]))
    transitions.append(fac.Transition(st_5, [
         ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_5, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_4._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_6, [
         ]))
    transitions.append(fac.Transition(st_7, [
         ]))
    st_5._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_6, [
        fac.UpdateInstruction(cc_1, True) ]))
    transitions.append(fac.Transition(st_7, [
        fac.UpdateInstruction(cc_1, False) ]))
    st_6._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_8, [
         ]))
    transitions.append(fac.Transition(st_9, [
         ]))
    transitions.append(fac.Transition(st_10, [
         ]))
    st_7._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_8, [
        fac.UpdateInstruction(cc_2, True) ]))
    transitions.append(fac.Transition(st_9, [
        fac.UpdateInstruction(cc_2, False) ]))
    transitions.append(fac.Transition(st_10, [
        fac.UpdateInstruction(cc_2, False) ]))
    st_8._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_9, [
        fac.UpdateInstruction(cc_3, True) ]))
    transitions.append(fac.Transition(st_10, [
        fac.UpdateInstruction(cc_3, False) ]))
    st_9._set_transitionSet(transitions)
    transitions = []
    st_10._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
EsitoFile_Type._Automaton = _BuildAutomaton_3()

