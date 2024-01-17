# ADDRESS PARSER  

This is an NLP++ Analyzer that parses through text and identifies addresses(in USPS formats) listed anywhere in the text. 

From the addresses, the following information is extracted(based on the type of address all or some of this information is extracted):
House number, Street Number, Street Name, Street Suffix(like ST- for street),Street type(like Lane or Road), city, state, pincode, type of address.

Additionally Rural Route and Highway Contract addresses are also parsed form which the information of Higway contract number/Rural Route and the Post box number is extracted.

All this information is made available in the json format. A sample output can be found(for the sample text) in input/text.text_log/output.json.

To run the analyzer, create a text file in input folder consisting of the text to be parsed.
