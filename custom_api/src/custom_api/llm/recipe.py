from langchain.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from custom_api.llm import LLMBase, LLMConfig


class RecipeResult(BaseModel):
    """Strukturiertes Rezept basierend auf verfügbaren Zutaten"""

    recipe_name: str = Field(description="Name des vorgeschlagenen Gerichts")
    description: str = Field(description="Kurze Beschreibung des Gerichts (1-2 Sätze)")
    cooking_time: str = Field(description="Zubereitungszeit (z.B. '30 Minuten')")
    difficulty: str = Field(description="Schwierigkeitsgrad: Einfach, Mittel oder Schwer")

    ingredients: list[str] = Field(description="Vollständige Zutatenliste mit Mengenangaben")
    instructions: list[str] = Field(description="Schritt-für-Schritt Kochanleitung")
    tips: list[str] = Field(description="Hilfreiche Kochtipps und Variationen")

    nutritional_info: str = Field(description="Kurze Nährwertangaben (Kalorien, besondere Eigenschaften)")


class RecipeAssistant(LLMBase):
    """KI-Kochassistent der aus verfügbaren Zutaten leckere Rezepte erstellt"""

    def get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["ingredients"],
            template="""Du bist ein erfahrener Koch und Rezeptentwickler. Du musst ALLE Felder der Antwort ausfüllen!

VERFÜGBARE ZUTATEN:
{ingredients}

Erstelle ein vollständiges Rezept mit ALLEN folgenden Feldern:

1. RECIPE_NAME: Ein kreativer, appetitlicher Name für das Gericht
2. DESCRIPTION: 1-2 Sätze die das Gericht beschreiben und appetitlich machen
3. COOKING_TIME: Realistische Zubereitungszeit (z.B. "25 Minuten", "1 Stunde 15 Minuten")
4. DIFFICULTY: Genau einer dieser Werte: "Einfach", "Mittel", "Schwer"
5. INGREDIENTS: Liste mit MINDESTENS 5-8 Zutaten mit exakten Mengenangaben
6. INSTRUCTIONS: Liste mit MINDESTENS 5-7 detaillierten Zubereitungsschritten
7. TIPS: Liste mit MINDESTENS 3-4 hilfreichen Kochtipps oder Variationen
8. NUTRITIONAL_INFO: Nährwertangaben und Besonderheiten (ca. 1-2 Sätze)

BEISPIEL STRUKTUR:
- recipe_name: "Cremige Tomaten-Basilikum-Pasta"
- description: "Ein aromatisches italienisches Gericht mit frischen Tomaten und Kräutern. Perfekt für ein schnelles Abendessen."
- cooking_time: "20 Minuten"
- difficulty: "Einfach"
- ingredients: ["250g Pasta", "400g gehackte Tomaten", "150ml Sahne", "2 Knoblauchzehen", "frisches Basilikum", "50g Parmesan", "2 EL Olivenöl", "Salz und Pfeffer"]
- instructions: ["Pasta in Salzwasser kochen", "Knoblauch in Öl anbraten", "Tomaten hinzufügen", "Sahne einrühren", "Pasta untermischen", "Mit Parmesan servieren"]
- tips: ["Pasta al dente kochen", "Basilikum erst am Ende hinzufügen", "Nudelwasser für Konsistenz nutzen"]
- nutritional_info: "Ca. 450 Kalorien pro Portion. Reich an Kohlenhydraten und Vitamin C."

WICHTIGE REGELN:
- Nutze hauptsächlich die verfügbaren Zutaten
- Ergänze Standard-Zutaten (Salz, Pfeffer, Öl) falls nötig
- Alle Mengenangaben müssen realistisch sein
- Jeder Schritt muss klar und verständlich sein
- Antworte komplett auf Deutsch
- FÜLLE ALLE FELDER AUS - keines darf leer bleiben!

Erstelle jetzt das vollständige Rezept:""",
        )

    async def predict(self, ingredients: str, temperature: float = 0.1, timeout: int = 8000) -> RecipeResult:
        """Erstellt ein Rezept basierend auf verfügbaren Zutaten"""
        model: Runnable = self.get_prompt() | self.get_client(
            model_config=LLMConfig(
                name="recipe-assistant",
                model_id="gpt-4.1",
                temperature=temperature,
                timeout=timeout,
            )
        ).with_structured_output(RecipeResult)

        return await model.ainvoke({"ingredients": ingredients})
