
"""
import xml.dom.minidom

from zcfd.utils import config


class ControlFile:
#    Control file handling functions
    def read_controlfile(self):
        dom = xml.dom.minidom.parse(config.controlfile)
        
    def create_controlfile(self):
        from xml.etree.ElementTree import Element, SubElement, Comment
        from zcfd.utils.XMLPretty import prettify

        top = Element('zcfd')

        comment = Comment('Generated for zCFD')
        top.append(comment)
        child = SubElement(top, 'SolverControl')
        nchild = SubElement(child, 'cycles')
        nchild.text = str(1000)
        nchild = SubElement(child, 'cfl')
        nchild.text = str(1.0)
        child = SubElement(top, 'Conditions')
        nchild = SubElement(child, 'mach')
        nchild.text = str(0.5)
        print prettify(top)
        f = open(config.controlfile, "w")
        f.write(prettify(top))
        
"""