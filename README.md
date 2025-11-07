# Wikidata and LiLa for Latin: Enabling Interoperability and Access to Inflected Forms and Corpus Attestations

DOI: [10.5281/zenodo.17553591](https://doi.org/10.5281/zenodo.17553591)

We are using [a Wikibase instance](https://lilamorph.wikibase.cloud) for publishing a Latin verb forms dataset, with the final goal of enriching Wikidata Latin lexemes, and for corpus annotation (matching tokens in morphologically annotated corpora to Wikibase forms).

In the following, we list links to SPARQL queries in the instance's query service.

* [1 Datasets on the Wikibase](https://lilamorph.wikibase.cloud/wiki/Main_Page#Datasets_on_this_Wikibase) 
  * [1.1 PrinParLat flexemes collection (lexicon version 1)](https://lilamorph.wikibase.cloud/wiki/Main_Page#PrinParLat_flexemes_collection_(lexicon_version_1)) 
  * [1.2 PrinParLat lexemes collection (lexicon version 2)](https://lilamorph.wikibase.cloud/wiki/Main_Page#PrinParLat_lexemes_collection_(lexicon_version_2)) 
  * [1.3 PrinParLat lexemes collection (lexicon version 3)](https://lilamorph.wikibase.cloud/wiki/Main_Page#PrinParLat_lexemes_collection_(lexicon_version_3)) 
  * [1.4 Index Thomisticus Treebank token collection](https://lilamorph.wikibase.cloud/wiki/Main_Page#Index_Thomisticus_Treebank_token_collection) 
    * [1.4.1 Tokens linked to more than one LiLa lemma](https://lilamorph.wikibase.cloud/wiki/Main_Page#Tokens_linked_to_more_than_one_LiLa_lemma) 
    * [1.4.2 Feature statistics](https://lilamorph.wikibase.cloud/wiki/Main_Page#Feature_statistics) 
* [2 Linking ITTB tokens to PrinParLat forms](https://lilamorph.wikibase.cloud/wiki/Main_Page#Linking_ITTB_tokens_to_PrinParLat_forms) 
  * [2.1 Linked vs. unlinked tokens: numbers](https://lilamorph.wikibase.cloud/wiki/Main_Page#Linked_vs._unlinked_tokens:_numbers) 
  * [2.2 Linked tokens](https://lilamorph.wikibase.cloud/wiki/Main_Page#Linked_tokens) 
    * [2.2.1 Unambiguously linked tokens](https://lilamorph.wikibase.cloud/wiki/Main_Page#Unambiguously_linked_tokens) 
    * [2.2.2 Ambiguously linked tokens](https://lilamorph.wikibase.cloud/wiki/Main_Page#Ambiguously_linked_tokens) 
      * [2.2.2.1 Form counts](https://lilamorph.wikibase.cloud/wiki/Main_Page#Form_counts) 
      * [2.2.2.2 List of ambiguous links](https://lilamorph.wikibase.cloud/wiki/Main_Page#List_of_ambiguous_links) 
    * [2.2.3 Linked forms frequency ranking](https://lilamorph.wikibase.cloud/wiki/Main_Page#Linked_forms_frequency_ranking) 
    * [2.2.4 Linked PrinParLat lexemes frequency ranking](https://lilamorph.wikibase.cloud/wiki/Main_Page#Linked_PrinParLat_lexemes_frequency_ranking) 
    * [2.2.5 Paralex cell frequency ranking](https://lilamorph.wikibase.cloud/wiki/Main_Page#Paralex_cell_frequency_ranking) 
  * [2.3 Unlinked tokens](https://lilamorph.wikibase.cloud/wiki/Main_Page#Unlinked_tokens) 
    * [2.3.1 PrinParLat lexemes: missing verbs](https://lilamorph.wikibase.cloud/wiki/Main_Page#PrinParLat_lexemes:_missing_verbs) 
* [3 Controlled vocabularies mappings](https://lilamorph.wikibase.cloud/wiki/Main_Page#Controlled_vocabularies_mappings) 
  * [3.1 PrinParLat morphological cell descriptors (Leipzig abbreviations)](https://lilamorph.wikibase.cloud/wiki/Main_Page#PrinParLat_morphological_cell_descriptors_(Leipzig_abbreviations)) 
  * [3.2 UDP morphological features for Latin](https://lilamorph.wikibase.cloud/wiki/Main_Page#UDP_morphological_features_for_Latin) 
  * [3.3 Paralex Cells](https://lilamorph.wikibase.cloud/wiki/Main_Page#Paralex_Cells) 
* [4 LiLaMorph Wikibase classes and properties](https://lilamorph.wikibase.cloud/wiki/Main_Page#LiLaMorph_Wikibase_classes_and_properties) 

## Python scripts in this repository

* [produce_prinparlat_lexemes.py](produce_prinparlat_lexemes.py)
   * Produces and uploads the Latin lexemes dictionary, version 3, including  forms conflation rules.

* [upload_ittb_token.py](upload_ittb_token.py)
   * Uploads token data.

* [match_token_form.py](match_token_form.py)
   * Matches tokens to lexeme forms.

* [match_token_lemmavariant_form.py](match_token_lemmavariant_form.py)
   * Matches tokens to variants of lexemes.

* [write_matches.py](write_matches.py)
   * Writes token-to-form links to Wikibase token items.

## Data sources and database queries

* [data/](data/) directory
  * "enhanced_forms" PrinParLat flexemes and lexemes collections source data
* [sparql/](sparql/) directory
  * LiLa database query for ITTB token data


