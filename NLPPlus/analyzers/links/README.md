# HYPERLINKS ANALYZER

This is an NLP++ Analyzer that parses through text and identifies any hyperlinks present in the text. A wide variety of link formats are recognized.

Some sample links can be found in input/text.txt

From each hyperlink,the information like:

- Scheme of the link(Like https(Secure Hypertext Tranfer Protocol), ftp(File Transfer Protocol))

- Domain-name(eg: wikipedia)
 
- Sub-domain(like en(English)/jp(Japanese) etc.)

- Page path

- Top Level Domain(like org/edu etc.)is extracted and made available in the json format.

A sample output can be found(for the sample text) in input/text.text_log/output.json.

To run the analyzer, create a text file in input folder consisting of the text to be parsed.
