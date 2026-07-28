1.Home directory includes:
 
1.1 src
 
	--- VHDL codes implementing RSA Public Key Cypher, along with a testbench. 

1.2 BasicRSA-T100.pdf 


2.Trojan
  
Trojan Description
  	
	The Trojan leaks the private secret key by replacing the cypher text when the input text plain is 32'h44444444.

Trojan Taxonomy

	Insertion phase: Design
	Abstraction level: Register-transfer level 
	Activation mechanism: Externally User Input
	Effects: Leak Information
	Location: Processor
	Physical characteristics: Functional

3. Implementation
	The RSA Public Key Cypher was evaluated in Xilinx ISE Design Suite 13.3.
