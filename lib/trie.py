
class Node(object):
    def __init__(self, s):
        self.value = s
        self.children = {}
        self.is_word = False
        
class Trie(object):
    def __init__(self):
        self.root = Node('')

    def _insert(self, word, parent):
        if not word:
            parent.is_word = True
            return
        try:
            c = word[0]
            node = parent.children[c]
        except KeyError:
            node = Node(parent.value + c)
            parent.children[c] = node
        self._insert(word[1:], node)

    def insert(self, word):
        self._insert(word.lower(), self.root)

    def _display(self, node, depth=1):
        q = [(node, depth)]
        prev = 1
        while q:
            n, d = q.pop(0)
            if d > prev:
                print ''
                prev = d
            spacing = ' '*(20/d)
            print "%s'%s'%s" %(spacing, n.value, spacing),
            for k in n.children.keys():
                q.append((n.children[k], d + 1))
        
##        if not node.children:
##            return
##        for k in node.children.keys():
##            self._display(node.children[k], depth + 1)

    def display(self):
        self._display(self.root)

    def load(self, filename):
        with open(filename, 'r') as f:
            for word in f.readlines():
                self.insert(word.strip('\n'))

    def _count(self, node):
        if not node.children:
            return 1
        r = 1
        for k in node.children.keys():
            r += self._count(node.children[k])
        return r
        

    def count(self):
        return self._count(self.root)

    def search(self, word):
        if not word:
            return
        q = [self.root]
        results = []
        try:
            while word:
                node = q.pop(0)
                c = word[0]
                q.append(node.children[c])
                word = word[1:]
            while q:
                node = q.pop(0)
                if not node.children or node.is_word:
                    results.append(node.value)
                    continue
                for k in node.children.keys():
                    q.append(node.children[k])
            return results
        except KeyError:
            print node.value
            return []
        
            
if __name__ == '__main__':
    T = Trie()
    try:
        T.load('words.txt')
    except:
        pass


