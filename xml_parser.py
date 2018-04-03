import xml.etree.ElementTree as XmlElementTree


def parser(response):
    if response:
        response_text = response.text
        xml = XmlElementTree.fromstring(response_text)

        if int(xml.attrib['success']) == 1:
            max_confidence = - float("inf")
            text = ''

            for child in xml:
                if float(child.attrib['confidence']) > max_confidence:
                    text = child.text
                    max_confidence = float(child.attrib['confidence'])

            if max_confidence != - float("inf"):
                return text
    else:
        return 'ЧТО ТО ПОШЛО НЕ ТАК БЛЯТЬ'
