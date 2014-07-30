expert-engine
=============

Expert Engine is a search engine for patent attorneys to find the most 
appropriate people to serve as expert witnesses. At present, attorneys 
must rely on their own personal networks to find experts. This is 
inefficient and does not necessarily guarantee a strong pairing of 
experts with cases. Expert Engine seeks to eliminate these 
inefficiencies. The model currently responsible for recommending them is 
very simple and does not take advantage of all of the rich data that 
patents offer. The code here is intended to improve the algorithm so 
that the service can be not only faster than the traditional method of 
finding an expert but also guarantee the recommendation of highly 
qualified people.

------------------------------------------------------------------------

Files contained in this repo:

#### basic_model.py
The framework of Scott's original CPC-based model, with the ability to 
alter the parameters and aggregation of groups of CPC scores.

#### cost_function.py
Computes the cost associated with a given model of predicting experts. 
The cost in this case is defined as the sum of the list indices where 
each "true" expert for a patent is found in the predictions for that
patent.

#### naive_bayes.py
Returns expert predictions based on basic [multinomial naive Bayes]
with [TF-IDF vectorizer].

#### patent_scraper.py
Scrapes and formats relevant patent data.

#### reference_scraper.py
Used for scraping networks of patent citations for eventual use in 
SimRank algorithm. Collects patent numbers of both in and out
references and inserts these into SQL tables.

#### sim_anneal_model.py
Optimizes parameters of basic model using [simulated annealing]
optimization.

#### simrank.py
Implements [SimRank] using [matrix operations]. 

------------------------------------------------------------------------

Intellectual Property Notice and Ownership

© 2014 Erin Burnside.  All rights reserved, exclusive of U.S. government 
works.

This project is subject to U.S. Patent Application Number 61973202. 

Scott Sherwin and Erin Burnside agree to assign (including executing any 
necessary formal documents) all intellectual property rights (including 
copyright, patent, and trademark rights) created during the scope of 
this project to Expert Engine upon its formation.

Neither the name Expert Engine nor the names of its contributors may be 
used to endorse or promote products related to this software without 
specific prior written permission.

[multinomial naive bayes]: http://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.MultinomialNB.html
[tf-idf vectorizer]: http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
[simulated annealing]: http://leonidzhukov.net/hse/2013/stochmod/papers/KirkpatrickGelattVecchi83.pdf
[simrank]: http://ilpubs.stanford.edu:8090/508/1/2001-41.pdf
[matrix operations]: http://www.cse.unsw.edu.au/~zhangw/files/wwwj.pdf
