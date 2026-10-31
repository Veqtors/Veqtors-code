# Results

Generated with tiktoken 0.14.0.

## token_probe.py

```
== cl100k_base vocab 100277
  1 tok  1 words 'hello' -> ['hello']
  1 tok  1 words ' hello' -> [' hello']
  1 tok  1 words 'Hello' -> ['Hello']
  2 tok  1 words 'HELLO' -> ['HEL', 'LO']
  2 tok  1 words 'tokenization' -> ['token', 'ization']
  3 tok  1 words 'unbelievably' -> ['un', 'belie', 'vably']
  2 tok  1 words 'Islamabad' -> ['Islam', 'abad']
  2 tok  1 words 'Karachi' -> ['Kar', 'achi']
  4 tok  1 words 'Peshawar' -> ['P', 'esh', 'aw', 'ar']
  3 tok  1 words '1234567' -> ['123', '456', '7']
  5 tok  1 words '12,345.67' -> ['12', ',', '345', '.', '67']
  5 tok  1 words '3.14159265' -> ['3', '.', '141', '592', '65']
  6 tok  1 words '2026-11-17' -> ['202', '6', '-', '11', '-', '17']
  2 tok  1 words '🙂' -> ['�', '��']
  7 tok  1 words '👩\u200d💻' -> ['�', '�', '�', '�', '�', '�', '�']
 11 tok  7 words 'def add(a, b):\n    return a + b' -> ['def', ' add', '(a', ',', ' b', '):\n', '   ', ' return', ' a', ' +', ' b']
 21 tok  6 words '{"name": "Imtiaz", "city": "Lahore", "active": tr -> ['{"', 'name', '":', ' "', 'Im', 't', 'iaz', '",', ' "', 'city', '":', ' "', 'L', 'ah', 'ore', '",'
 13 tok  6 words 'name: Imtiaz\ncity: Lahore\nactive: true' -> ['name', ':', ' Im', 't', 'iaz', '\n', 'city', ':', ' Lahore', '\n', 'active', ':', ' true']
 18 tok  1 words 'https://github.com/veqtors/Veqtors-code/tree/main -> ['https', '://', 'github', '.com', '/', 've', 'qt', 'ors', '/V', 'eq', 'tors', '-code', '/tree', '/
  7 tok  6 words 'The capital of Pakistan is Islamabad.' -> ['The', ' capital', ' of', ' Pakistan', ' is', ' Islamabad', '.']
 30 tok  6 words 'پاکستان کا دارالحکومت اسلام آباد ہے۔' -> ['پ', 'ا', 'ک', 'ست', 'ان', ' ک', 'ا', ' د', 'ار', 'ال', 'ح', 'ک', 'و', 'م', 'ت', ' ا', 'س', 'ل', 'ام', ' �', '
== o200k_base vocab 200019
  1 tok  1 words 'hello' -> ['hello']
  1 tok  1 words ' hello' -> [' hello']
  1 tok  1 words 'Hello' -> ['Hello']
  2 tok  1 words 'HELLO' -> ['HEL', 'LO']
  2 tok  1 words 'tokenization' -> ['token', 'ization']
  3 tok  1 words 'unbelievably' -> ['un', 'bel', 'ievably']
  2 tok  1 words 'Islamabad' -> ['Islam', 'abad']
  2 tok  1 words 'Karachi' -> ['Kar', 'achi']
  3 tok  1 words 'Peshawar' -> ['P', 'esh', 'awar']
  3 tok  1 words '1234567' -> ['123', '456', '7']
  5 tok  1 words '12,345.67' -> ['12', ',', '345', '.', '67']
  5 tok  1 words '3.14159265' -> ['3', '.', '141', '592', '65']
  6 tok  1 words '2026-11-17' -> ['202', '6', '-', '11', '-', '17']
  1 tok  1 words '🙂' -> ['🙂']
  5 tok  1 words '👩\u200d💻' -> ['�', '�', '\u200d', '�', '�']
 11 tok  7 words 'def add(a, b):\n    return a + b' -> ['def', ' add', '(a', ',', ' b', '):\n', '   ', ' return', ' a', ' +', ' b']
 21 tok  6 words '{"name": "Imtiaz", "city": "Lahore", "active": tr -> ['{"', 'name', '":', ' "', 'Im', 't', 'iaz', '",', ' "', 'city', '":', ' "', 'L', 'ah', 'ore', '",'
 13 tok  6 words 'name: Imtiaz\ncity: Lahore\nactive: true' -> ['name', ':', ' Im', 't', 'iaz', '\n', 'city', ':', ' Lahore', '\n', 'active', ':', ' true']
 18 tok  1 words 'https://github.com/veqtors/Veqtors-code/tree/main -> ['https', '://', 'github', '.com', '/', 've', 'qt', 'ors', '/V', 'eq', 'tors', '-code', '/tree', '/
  7 tok  6 words 'The capital of Pakistan is Islamabad.' -> ['The', ' capital', ' of', ' Pakistan', ' is', ' Islamabad', '.']
 10 tok  6 words 'پاکستان کا دارالحکومت اسلام آباد ہے۔' -> ['پاکستان', ' کا', ' دار', 'الح', 'ک', 'ومت', ' اسلام', ' آباد', ' ہے', '۔']
```

## bpe_toy.py

```
start: 11 tokens: [' ', 'd', 'e', 'i', 'l', 'n', 'o', 'r', 's', 't', 'w']
step 1: merge ' ' + 'l' (seen 6x) -> ' l'
step 2: merge ' l' + 'o' (seen 6x) -> ' lo'
step 3: merge ' lo' + 'w' (seen 6x) -> ' low'
step 4: merge 'e' + 's' (seen 5x) -> 'es'
step 5: merge 'es' + 't' (seen 5x) -> 'est'
step 6: merge ' ' + 'n' (seen 3x) -> ' n'

final split of each distinct word:
  ' low': [' low'] = 1 tokens
  ' lower': [' low', 'e', 'r'] = 3 tokens
  ' newest': [' n', 'e', 'w', 'est'] = 4 tokens
  ' widest': [' ', 'w', 'i', 'd', 'est'] = 5 tokens
  'low' (no leading space): ['l', 'o', 'w'] = 3 tokens
```

## cost_my_prompt.py

```
20 records as JSON (422 words)
  cl100k_base: 1122 tokens
  o200k_base: 1122 tokens
20 records as key: value lines (380 words)
  cl100k_base: 780 tokens
  o200k_base: 780 tokens
```

## English rule of thumb, measured

Issue 1's draft (technical English in markdown, with code blocks, equations and URLs stripped): 2,823 words.

- cl100k_base: 4,416 tokens, 1.56 per word
- o200k_base: 4,355 tokens, 1.54 per word
