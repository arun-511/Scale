from re import search, compile, sub
from difflib import SequenceMatcher

class Resolve():
    def __init__(self):
        self._bracket = 0
        self._block   = 0
        self._dashed  = 0
        self._artist  = 0
        
    def decode(self, string):
        return string.encode("ascii", errors="ignore").decode()
        
    def resolve_block(self, string):
        format = compile(r"(?P<a>.+)\[(?P<b>.+)\]")
        while True:
            resolve = format.search(string)
            if resolve:
                self._block = resolve.group('b').strip()
                string      = resolve.group('a').strip()
            else:
                break
        return string
                
    def resolve_bracket(self, string):
        format = compile(r"(?P<a>.+)\((?P<b>.+)\)")
        while True:
            resolve = format.search(string)
            if resolve:
                self._bracket = resolve.group('b').strip()
                string        = resolve.group('a').strip()
            else:
                break
        return string
        
    def resolve_dots(self, string):
        try:
            int(string[:string.find(".")])
            string = string[string.find(".") + 1:]
            return string.strip()
        except:
            return string
        
    def resolve_dash(self, string):
        format = compile(r"(?P<l>.+)- (?P<r>.+)")
        resolve = format.search(string)
        if resolve:
            left  = resolve.group('l').strip()
            right = resolve.group('r').strip()
            if self._artist.lower() in right.lower():
                return left
            elif len(right) < 3:
                return left
            else:
                self._dashed = left.replace(self._artist, " ").strip()
                return right
        return string
        
    def title(self, title, user):
        self._artist = user
        
        title = self.resolve_block(title)
        title = self.resolve_bracket(title)
        title = self.resolve_dash(title)
        title = self.resolve_dots(title)
        
        if self._bracket:
            title = "%s (%s)" % (title, self._bracket)
            
        elif not self._block and self._dashed:
            if "ft." in self._dashed:
                title = "%s (%s)" % (title, self._dashed)
            
            
        return sub("\s+", " ", self.decode(title).strip())
                
    def album(self, album, user):
        self._artist = user
        
        album = self.resolve_block(album)
        album = self.resolve_bracket(album)
        album = self.resolve_dash(album)
        
        return sub("\s+", " ", self.decode(album).strip())
        
    def artist(self, artist):
        return sub("\s+", " ", self.decode(artist).strip())
        

"""
t = "BIGWAVE ft. N0BHT - Respite"
u = "BIGWAVE"

print(Resolve().title(t, u))
"""
