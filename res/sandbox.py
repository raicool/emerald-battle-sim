import charmap

def CHARMAP():
    out: str = str(
          "map: dict[int, int] = {"
    )
    for entry in charmap.map.items():
        out += f"\n\t{hex(ord(entry[0]))}: {hex(entry[1])},"
        pass
    out += "\n}"
    print(out)

def main():
	idx: int = 1
	with open("res/charmap.txt") as file:
		for line in file:
			line = line.rsplit()[0]
			line += f" = {idx},"
			idx += 1
			print(line)

if (__name__ == "__main__"):
	main()