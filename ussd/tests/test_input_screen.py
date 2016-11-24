from django.test import LiveServerTestCase
import staticconf
from django.urls import reverse

from ussd.core import validate_ussd_journey
import requests
import uuid
from ussd.tests.sample_screen_definition import path


class TestInputHandler(LiveServerTestCase):

    def make_request(self, session_id, ussd_input, phone_number, language='en'):
        url = self.live_server_url + \
        reverse('africastalking_url')

        print(url)
        response = requests.post(
            url=url,
            data={
                "sessionId": session_id,
                "text": ussd_input,
                "phoneNumber": phone_number,
                "serviceCode": "test",
                "language": language
            }
        )
        return response

    def test_showing_screen_content(self):
        session_id = str(uuid.uuid4())
        # dial in
        response = self.make_request(
            session_id,
            '',
            '200'
        )

        self.assertEqual(
            "Enter your height\n",
            response.content.decode()
        )

        # enter height
        response = self.make_request(
            session_id, '6', '200'
        )

        self.assertEqual(
            "Enter your age\n",
            response.content.decode()
        )

        # enter age

        response = self.make_request(
            session_id, '24', '200'
        )

        self.assertEqual(
            "Your age is 24 and your height is 6.\n"
            "Enter anything to go back to the first screen\n",
            response.content.decode()
        )

    def test_multilanguage_support(self):
        session_id = str(uuid.uuid4())
        # Dial in
        response = self.make_request(session_id, '1', '200', 'sw')

        self.assertEqual(
            "Weka ukubwa lako\n",
            response.content.decode()
        )

        response = self.make_request(session_id, '7', '200', 'sw')

        self.assertEqual(
            "Weka miaka yako\n",
            response.content.decode()
        )

        response = self.make_request(session_id, '23', '200', 'sw')

        self.assertEqual(
            "Miaka yako in 23 na ukubwa wako in 7.\n"
            "Weka kitu ingine yoyote unende "
            "kwenye screen ya kwanza\n",
            response.content.decode()
        )
    def test_input_validation(self):
        session_id = str(uuid.uuid4())

        # dial in
        response = self.make_request(
            session_id, '', '200'
        )

        # enter invalid height
        response = self.make_request(
            session_id, 'mwas', '200'
        )

        # should get a invalid error message
        self.assertEqual(
            "Enter number between 1 and 7\n",
            response.content.decode()
        )

        # enter valid height
        response = self.make_request(session_id, '6', '200')

        self.assertEqual(
            "Enter your age\n",
            response.content.decode()
        )

        # enter invalid age greater thatn 100
        response = self.make_request(session_id, '150', '200')

        self.assertEqual(
            "Number over 100 is not allowed\n",
            response.content.decode()
        )

        # enter a valid age
        response = self.make_request(session_id, '23', '200')

        self.assertEqual(
            "Your age is 23 and your height is 6.\n"
            "Enter anything to go back to the first screen\n",
            response.content.decode()
        )

    def test_using_input_validation_yaml(self):
        # load yaml file
        staticconf.YamlConfiguration(
            path + '/valid_input_screen_conf.yml',
            namespace='TestInputHappyCase',
            flatten=False)

        ussd_screens = staticconf.config.\
            get_namespace('ussd_content').\
            get_config_values()

        self.assertTrue(
            validate_ussd_journey(ussd_screens)
        )

    def test_validating_invalid_yaml(self):
        staticconf.YamlConfiguration(
            path + '/valid_input_screen_conf.yml',
            namespace='TestInputHappyCase',
            flatten=False)

        ussd_screens = staticconf.config.\
            get_namespace('ussd_content_1').\
            get_config_values()

        validation_results = validate_ussd_journey(ussd_screens)

        self.assertFalse(
            validation_results
        )

        self.assertEqual(3, len(validation_results))

        expected_results = dict(
            enter_height={
                "validators": "Invalid validation, "
                              "error message required"
            },
            enter_age={
                "input_identifier": "required field missing",
                "text": "Invalid text, should be a dictionary with"
                        " languages and a default language"
            },
            show_infomation={
                "next_screen": "required field missing"
            },
            initial_screen="required field missing"
        )

        self.assertDictEqual(validation_results, expected_results)
