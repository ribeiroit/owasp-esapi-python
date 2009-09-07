#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@license: OWASP Enterprise Security API (ESAPI)
     
    This file is part of the Open Web Application Security Project (OWASP)
    Enterprise Security API (ESAPI) project. For details, please see
    U{http://www.owasp.org/index.php/ESAPI<http://www.owasp.org/index.php/ESAPI>}.

    The ESAPI is published by OWASP under the BSD license. You should read and 
    accept the LICENSE before you use, modify, and/or redistribute this software.
    
@summary: The Encryptor interface provides a set of methods for performing 
    common encryption and hashing operations. 
@copyright: Copyright (c) 2009 - The OWASP Foundation
@author: Craig Younkins (craig.younkins@owasp.org)
"""

import esapi.codecs.codec as codec
from esapi.encoder import Encoder

class VBScriptCodec(codec.Codec):
    """
    Implementation of the Codec interface for 'quote' encoding from VBScript.
    """
   
    def __init__(self):
        """
        Instantiates the VBScript codec.
        """
        codec.Codec.__init__(self)
        
    def encode(self, immune, input_):
        buf = ''
        encoding = False
        inquotes = False
        
        try:
            for i in range(len(input_)):
                char = input_[i]
                # handle normal characters and surround them with quotes
                if char in Encoder.CHAR_ALPHANUMERICS or char in immune:
                    if encoding and i > 0:
                        buf += "&"
                    if not inquotes and i > 0:
                        buf += '"'
                    buf += char
                    inquotes = True
                    encoding = False
                    
                # handle characters than need encoding
                else:
                    if inquotes:
                        buf += '"'
                    if i > 0:
                        buf += "&"
                    buf += self.encode_character(immune, char)
                    inquotes = False
                    encoding = True
        except TypeError:
            return None
                
        return buf
    
    def encode_character(self, immune, char):
        """
        Returns a quote-encoded character.
        """
        # Check for immunes
        if char in immune:
            return char
            
        # Only look at 8-bit 
        if not codec.is_8bit(char):
            return char
        
        # Pass alphanumerics
        if char.isalnum():  
            return char
            
        return "chrw(" + str(ord(char)) + ")"
    
    def decode_character(self, pbs):
        """
        Returns the decoded version of the character starting at index, or
        None if no decoding is possible.
	  
        Formats all are legal both upper/lower case:
            - "x - all special characters
            - chrw(x)
        """
        pbs.mark()
        
        first = pbs.next()
        if first is None:
            pbs.reset()
            return None
            
        # if this is not an encoded character, return None
        if first == '"':
            second = pbs.next()           
            return second
        elif first == 'c':
            # could be chrw(x)
            next_4 = ''.join([pbs.next() for x in range(4)])
            if next_4 == 'hrw(':
                num_buf = ''
                for i in range(4):
                    # Look for a maximum of 4 digits afterwards
                    next_num = pbs.next()
                    if next_num is not None and next_num.isdigit():
                        num_buf += next_num
                    else:
                        pbs.pushback(next_num)
                        break
                if not pbs.peek(')'):
                    # Something isn't right here
                    pbs.reset()
                    return None
                # Eat the end paren
                pbs.next()
                # Try to convert to number
                try:
                    decoded = unichr(int(num_buf))
                    return decoded
                except ValueError:
                    pbs.reset()
                    return None
            else:
                # fall through to reset and return None
                pass
        
        pbs.reset()
        return None
        