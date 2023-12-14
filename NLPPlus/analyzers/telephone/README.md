# TELEPHONE ANALYZER
This is an NLP++ Analyzer that parses through text and identifies Telephone numbers listed in the text. Some sample telephone number formats can be found in input/text.txt

Here are some examples
- 212.456.7890
- 212 456 7890
- +12124567890
- +12124567890
- +1 212.456.7890
- +212-456-7890
- 1-212-456-7890

For each telephone number identified in the text, the following information is extracted:

- the text identified
- area
- prefix of the number
- station value
- the type of the telephone(mobile/landline).

To run the analyzer, create a text file in the input folder consisting of the text to be parsed.
