# NLPPlus
This is Python package for NLP Engine. It uses nlp-engine as DLL. You could find detailed documentation about nlp-engine here https://github.com/VisualText/nlp-engine.

## Requirements 
* Python 3.9 x64 or later
* Windows 10 x64 or later

## Using the Library
1. This library has two functions
```
import NLPPlus

NLPPlus.set_working_folder("path_to_working_folder")
parser = "parse-en-us"

NLPPlus.analyze(parser=parser, str="string_to_analyze")
```

2. Set your working folder
The folder should include "analyzers" folder and "data" folder. In analyzer folder, there should be parsers as folders. By default, it sets working folder as the installed package folder and there are "parse-en-us" parser and you can use it.

3. Result
NLPPlus.analyze() returns the analyzed result as an XML format.
