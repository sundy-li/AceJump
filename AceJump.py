import sublime, sublime_plugin
import time

begin_char = 'a'
match_char_length = 26
letters = [chr(x + ord(begin_char)) for x in range(match_char_length)]
regexp = r"{0}[\d\w]*"

is_mark = False
words = []

##load settings
settings = sublime.load_settings("ace_jump.sublime-settings")

## hash the number to string
def number_to_string(num):
	str = ""
	if num == 0:
		return begin_char

	while num:
		str += letters[int(num % match_char_length)]
		num //= match_char_length
	return str[::-1]

def string_to_num(str):
	num = 0
	for s in str:
		num = num * match_char_length + (ord(s) - ord(begin_char))

	return num

class AceJumperCommand(sublime_plugin.WindowCommand):

	def run(self):
		global settings
		self.hint_length = settings.get("hint_length")
		print(self.hint_length, "---")
		self.view = self.window.active_view()
		self.back()
		## wheter has modify the view
		self.str = ""

		## the labels shows that where the characters we are looking for may be in
		self.labels = False
		self.window.show_input_panel(
			"AceJump", "",
			self.done, self.change, self.cancel
			)

	def done(self, command):
		self.cancel()
		self.jump(command)
		sublime.set_timeout(self.view.run_command("ace_tmp"),4000)
		

	def change(self, command):
		if not command:
			self.back()
		elif len(command) == self.hint_length:
			self.cancel()
			self.str = command
			self.view.run_command("ace_mark" , {"char" : command})
		elif len(command) > self.hint_length:
			self.jump(command)

	def cancel(self):
		if is_mark:
			self.view.run_command("ace_un_mark")
		self.view.erase_status("AceJump")
		sublime.status_message("AceJump: Cancelled")

	def jump(self, command):
		index = string_to_num(command[self.hint_length:])
		if (index >= 0) :
			global words
			region = words[index]
			self.view.run_command("ace_jump_to_place" , {"index" : region.begin()})

	def back(self):
		self.str = ""
		self.view.run_command("ace_un_mark")



class AceMarkCommand(sublime_plugin.TextCommand):
	

	def run(self,edit,char):
		global is_mark
		if is_mark:
			self.view.run_command("ace_un_mark")
		global words # :\
		# Find words in this region
		mark_regions = []
		visible_region = self.view.visible_region()
		num = 0
		words = []
		visible_region = self.view.visible_region()
		pos = visible_region.begin()
		last_pos = visible_region.end()
		while pos < last_pos :
			word = self.view.find(regexp.format(char), pos , sublime.IGNORECASE)
			if word:
				words.append(word)
				tmp_mark_wds = number_to_string(num)
				tmp_mark_wds_len = len(tmp_mark_wds)
				##conside charaction \n
				replace_region = sublime.Region(word.begin(), word.begin() + tmp_mark_wds_len)
				self.view.replace(edit, replace_region, tmp_mark_wds)
				mark_regions.append(replace_region)
				num = num + 1
			else:
				break
			pos = word.end()

		matches = len(words)
		if not matches:
			self.view.set_status("AceJump", "No matches found")
			return
		is_mark = True
		# Which scope to use here, string?
		# comment, string
		self.view.add_regions("AceJumpMarks", mark_regions, "string")
		self.view.set_status(
			"AceJump", "Found {} match{} for character {}".format(matches, "es" if matches > 1 else "", char)
		)



class AceUnMarkCommand(sublime_plugin.TextCommand):
	def run(self,edit):
		global is_mark
		if is_mark:
			self.view.erase_regions("AceJumpMarks")
			self.view.erase_regions("mark_line")
			self.view.end_edit(edit)
			self.view.run_command("undo")
			is_mark = False


class AceJumpToPlaceCommand(sublime_plugin.TextCommand):

	def run(self, edit, index):
		## add marks 
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(index))

		self.view.add_regions("mark_line", [sublime.Region(index,index)], "string", "bookmark")
		self.view.show(index)


class AceTmpCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		## add marks 
		self.view.erase_regions("mark_line")
