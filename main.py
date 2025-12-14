import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import pyjokes
import sys


# detect whether PyAudio is available (used by speech_recognition Microphone)
try:
	import pyaudio  # type: ignore
	HAS_PYAUDIO = True
except Exception:
	HAS_PYAUDIO = False


def init_tts(rate=150, volume=1.0):
	engine = pyttsx3.init()
	engine.setProperty('rate', rate)
	engine.setProperty('volume', volume)
	return engine


def speak(engine, text):
	engine.say(text)
	engine.runAndWait()


def listen(recognizer, microphone, timeout=5, phrase_time_limit=7):
	with microphone as source:
		recognizer.adjust_for_ambient_noise(source, duration=0.5)
		try:
			audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
		except sr.WaitTimeoutError:
			return None
	try:
		return recognizer.recognize_google(audio)
	except sr.UnknownValueError:
		return None
	except sr.RequestError as e:
		# propagate RequestError to allow caller to handle service/unavailability
		raise


def handle_command(text, engine):
	text = text.lower()
	if 'time' in text:
		now = datetime.datetime.now().strftime('%I:%M %p')
		resp = f"The time is {now}."
		speak(engine, resp)
		return

	if 'joke' in text or 'tell me a joke' in text:
		joke = pyjokes.get_joke()
		speak(engine, joke)
		return

	if text.startswith('search for') or text.startswith('search'):
		# extract query
		q = text.replace('search for', '').replace('search', '').strip()
		if not q:
			speak(engine, 'What should I search for?')
			return
		url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
		speak(engine, f'Searching for {q}')
		webbrowser.open(url)
		return

	if text.startswith('open'):
		# try to open a website or phrase
		target = text.replace('open', '').strip()
		if not target:
			speak(engine, 'What should I open?')
			return
		if '.' in target or 'http' in target:
			url = target if target.startswith('http') else f'http://{target}'
		else:
			url = f'https://www.google.com/search?q={target.replace(" ", "+")}'
		speak(engine, f'Opening {target}')
		webbrowser.open(url)
		return

	if text in ('exit', 'quit', 'stop', 'goodbye'):
		speak(engine, 'Goodbye!')
		sys.exit(0)

	# fallback: echo
	speak(engine, f'You said: {text}')


def main():
	recognizer = sr.Recognizer()
	engine = init_tts()

	if not HAS_PYAUDIO:
		print('Warning: PyAudio is not installed — microphone unavailable.')
		speak(engine, 'PyAudio is not installed. Switching to text input mode.')
		# fallback: text input loop
		while True:
			try:
				text = input('Type a command (or "exit"): ').strip()
			except (KeyboardInterrupt, EOFError):
				print('\nExiting.')
				break
			if not text:
				continue
			handle_command(text, engine)
		return

	# normal microphone mode
	try:
		microphone = sr.Microphone()
	except Exception as e:
		print('Microphone not found or not accessible:', e)
		speak(engine, 'Microphone not accessible. Switching to text input mode.')
		while True:
			try:
				text = input('Type a command (or "exit"): ').strip()
			except (KeyboardInterrupt, EOFError):
				print('\nExiting.')
				break
			if not text:
				continue
			handle_command(text, engine)
		return

	speak(engine, 'Voice assistant started. Say a command or say exit to quit.')

	while True:
		print('Listening... (say something)')
		try:
			text = listen(recognizer, microphone)
		except sr.RequestError as e:
			# network / Google API error
			msg = 'Speech recognition service unavailable. Switching to text input mode.'
			print('RequestError from recognizer:', e)
			speak(engine, msg)
			# fallback to text input loop
			while True:
				try:
					text = input('Type a command (or "exit"): ').strip()
				except (KeyboardInterrupt, EOFError):
					print('\nExiting.')
					return
				if not text:
					continue
				handle_command(text, engine)
			return
		if text is None:
			speak(engine, "I didn't catch that. Please try again.")
			continue
		print('Heard:', text)
		handle_command(text, engine)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('\nExiting.')
