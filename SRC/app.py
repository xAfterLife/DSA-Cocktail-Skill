# -*- coding: utf-8 -*-
import logging
import traceback
import ask_sdk_core.utils as ask_utils
import requests
import random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Hier definiere ich die Variablen für die "Session"
current_drink = None

def data_from_response(response):
    if response.status_code == 200:
        data = response.json()
        if data['drinks'] is None:
            data = None
    return data

def get_random_cocktail(url):
    response = requests.get(url.replace(" ", "%20"))
    data = data_from_response(response)

    if data != None:
        id_Drink = data['drinks'][random.randint(0, len(data['drinks']) - 1)]['idDrink']
        response = requests.get(f'https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i={id_Drink}'.replace(" ", "%20"))
        data = data_from_response(response)
    return data

def get_user_name(handler_input):
    access_token = handler_input.request_envelope.context.system.user.access_token

    if access_token:
        api_endpoint = 'https://api.amazonalexa.com/v2/accounts/~current/settings/Profile.name'
        headers = { "Authorization": f"Bearer {access_token}" }
        response = requests.get(api_endpoint, headers=headers)

        if response.status_code == 200:
            return response.json().get("first_name")
    return None


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        username = get_user_name(handler_input)
        if username is None:
            speak_output = "Wie kann ich helfen?"
        else:
            speak_output = f"{username} wie kann ich helfen?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class IngredientIntentHandler(AbstractRequestHandler):
    """Handler for Random Cocktail Intent."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("IngredientIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global current_drink

        if current_drink is None:
            speak_output = "Um welchen Drink handelt es sich denn?"
        else:
            speak_output = self.get_ingredients()

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
    
    def get_ingredients(self):
        drink_name = current_drink['drinks'][0]['strDrink']
        output = ""

        for i in range(1,16):
            ingredient_field = "strIngredient" + str(i)
            ingredient = current_drink["drinks"][0].get(ingredient_field, "")

            measurement_field = "strMeasure" + str(i)
            measure = current_drink["drinks"][0].get(measurement_field, "")

            if ingredient and measure:
                output += f"{measure} {ingredient}; "
        return f"Inhaltsstoffe für einen {drink_name}: " + output


class InstructionIntentHandler(AbstractRequestHandler):
    """Handler for Random Cocktail Intent."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("InstructionIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global current_drink

        if current_drink is None:
            speak_output = "Um welchen Drink handelt es sich denn?"
        else:
            speak_output = self.cocktail_rezept()

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

    def cocktail_rezept(self):
        global current_drink

        drink_name = current_drink['drinks'][0]['strDrink']

        if(current_drink["drinks"][0]["strInstructionsDE"] is None):
            recipe = current_drink["drinks"][0]["strInstructions"]
        else:
            recipe = current_drink["drinks"][0]["strInstructionsDE"]
        return (f"Das Rezept für einen {drink_name}: {recipe}")

class NonAlcoholicRandomIntentHandler(AbstractRequestHandler):
    """Handler for Random Cocktail Intent."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("NonAlcoholicRandomIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global current_drink
        current_drink = get_random_cocktail("https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Non_Alcoholic")
        drink_name = current_drink['drinks'][0]['strDrink']

        speak_output = f'Der zufällige Alkoholfreie Cocktail, den ich für dich gefunden habe, ist {drink_name}.'
        
        # Erstelle eine Antwort für Alexa, die den Namen des Cocktails enthält
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class RandomCocktailIntentHandler(AbstractRequestHandler):
    """Handler for Random Cocktail Intent."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("RandomCocktailIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global current_drink
        current_drink = get_random_cocktail("https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Alcoholic")
        drink_name = current_drink['drinks'][0]['strDrink']

        speak_output = f'Der zufällige Alkoholhaltige Cocktail, den ich für dich gefunden habe, ist {drink_name}.'
        
        # Erstelle eine Antwort für Alexa, die den Namen des Cocktails enthält
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GetByIngredientIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetByIngredientIntent")(handler_input)

    def handle(self, handler_input):
        global current_drink

        ingridient = handler_input.request_envelope.request.intent.slots["Ingredient"].value
        current_drink = get_random_cocktail(f"https://www.thecocktaildb.com/api/json/v1/1/filter.php?i={ingridient}".replace(" ", "%20"))

        if current_drink == None:
            speak_output = f"Kein Cocktail mit {ingridient} gefunden, versuche deinen Inhaltsstoff auf Englisch zu suchen"
        else:
            drink_name = current_drink['drinks'][0]['strDrink']
            speak_output = f"Ein Vorschlag für einen Cocktail mit {ingridient} wäre ein {drink_name}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GetCocktailNameIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetCocktailNameIntent")(handler_input)

    def handle(self, handler_input):
        global current_drink

        drink_name = handler_input.request_envelope.request.intent.slots["Cocktail_Name"].value
        current_drink = self.cocktail_from_name(drink_name)
        
        if current_drink is None:
            speak_output = f"{drink_name} nicht gefunden, versuche einen anderen Cocktail"
        else:
            speak_output = f"Du hast den Cocktail {drink_name} ausgewählt."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
    
    def cocktail_from_name(self, cocktail_name):
        response = requests.get(f'https://www.thecocktaildb.com/api/json/v1/1/search.php?s={cocktail_name}'.replace(" ", "%20"))
        return data_from_response(response)

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Bis zum nächsten mal"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        global current_drink

        # Any cleanup logic goes here.
        current_drink = None

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(traceback.format_exc(), exc_info=True)

        speak_output = str(exception)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())

# Add Intent Modules
sb.add_request_handler(RandomCocktailIntentHandler())
sb.add_request_handler(InstructionIntentHandler())
sb.add_request_handler(IngredientIntentHandler())
sb.add_request_handler(GetCocktailNameIntentHandler())
sb.add_request_handler(GetByIngredientIntentHandler())
sb.add_request_handler(NonAlcoholicRandomIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()