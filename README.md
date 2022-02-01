# CoSearcher

This repository holds the source code for the ECIR 2021 paper [Studying the Effectiveness of Conversational Search Refinement Through User Simulation](https://link.springer.com/chapter/10.1007%2F978-3-030-72113-8_39).

## Installation

```sh
git clone https://github.com/amzn/cosearcher
cd cosearcher
scripts/bootstrap.sh
```

## Usage

```sh
# Qulac facets with patience = 3 and cooperativeness = 1.0
python3 src/main.py > dialogues.json

# S-Bing facets with patience = 5 and cooperativeness = 0.5
# Get your API_KEY at https://www.microsoft.com/en-us/bing/apis/bing-autosuggest-api.
# Free usage is restricted to one call every 3 seconds (--bing-sleep)
python3 src/main.py --facet bing --bing-key API_KEY --bing-sleep 3 --patience 5 --cooperativeness 0.5 > dialogues.json

# B-Bing facets with patience = 5 and cooperativeness decreasing from 1
python3 src/main.py --facet graph-bing --bing-key API_KEY --bing-sleep 3 --patience 5 --cooperativeness 0.5 --cooperativeness-fn dec > dialogues.json
```

These commands output a large JSON object containing all simulated dialogues and IR results. To extract all IR metrics for the entire simulation, use [jq](https://github.com/stedolan/jq):

```sh
jq .metrics dialogues.json
```

## Customization

Both the agent (class `Clarify`) and CoSearcher (class `UserSimulator`) use various components that inherit from abstract classes. You can customize the system by creating your own implementations of these abstract classes and modifying `main.py` to inject your implementations.

For example, you can create a *stubborn* answer generator by inheriting from `AnswerGenerator` as follows:
```python
# from src/answer_generation.py
class AnswerGenerator(ABC):
    @abstractmethod
    def generate_answer(self, topic: clarify_types.Topic, facet: clarify_types.Facet, cooperativeness: float, similarity: float) -> str:
        pass

# your code
class StubbornAnswerGenerator(AnswerGenerator):
    def generate_answer(self, topic: clarify_types.Topic, facet: clarify_types.Facet, cooperativeness: float, similarity: float) -> str:
        return "no"
```

## Citing

If you use this code in your work, please cite:

```
@InProceedings{salleetal2021cosearcher,
    author="Salle, Alexandre
    and Malmasi, Shervin
    and Rokhlenko, Oleg
    and Agichtein, Eugene",
    editor="Hiemstra, Djoerd
    and Moens, Marie-Francine
    and Mothe, Josiane
    and Perego, Raffaele
    and Potthast, Martin
    and Sebastiani, Fabrizio",
    title="Studying the Effectiveness of Conversational Search Refinement Through User Simulation",
    booktitle="Advances in  Information Retrieval",
    year="2021",
    publisher="Springer International Publishing",
    address="Cham",
    pages="587--602",
    abstract="A key application of conversational search is refining a user's search intent by asking a series of clarification questions, aiming to improve the relevance of search results. Training and evaluating such conversational systems currently requires human participation, making it unfeasible to examine a wide range of user behaviors. To support robust training/evaluation of such systems, we propose a simulation framework called CoSearcher (Information about code/resources available at https://github.com/alexandres/CoSearcher.) that includes a parameterized user simulator controlling key behavioral factors like cooperativeness and patience. Using a standard conversational query clarification benchmark, we experiment with a range of user behaviors, semantic policies, and dynamic facet generation. Our results quantify the effects of user behaviors, and identify critical conditions required for conversational search refinement to be effective.",
    isbn="978-3-030-72113-8"
}
```
