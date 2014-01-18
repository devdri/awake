import Image, struct, sys

cart_name = sys.argv[1]
f = open(cart_name, 'rb')
data = f.read()
f.close()

size = len(data)
row = 32
tiles_per_row = row/2
tiles_width = tiles_per_row*8

full_W = row+tiles_width+256
H = size/row

img = Image.new('RGB', (full_W, H))

def get_byte(addr):
	if addr < len(data):
		ch = data[addr]
		return struct.unpack('b', ch)[0]
	else:
		return 0

def put_pixel(x, y, val):
	img.putpixel((x, y), val)

def render_line(base, x, y):
	lo = get_byte(base)
	hi = get_byte(base+1)

	for i in range(8):
		col_lo = (lo >> i) & 1
		col_hi = (hi >> i) & 1
		col = col_hi << 1 | col_lo

		colmap = ((255, 255, 255), (200, 200, 200), (100, 100, 100), (0, 0, 0))
		put_pixel(x + 7-i, y, colmap[col])

def render_sprite(base, x, y):
	for i in range(8):
		render_line(base + (i*2), x, y+i)

def render_sprite_sheet(w, h):
	base = 0
	for i in range(h):
		for j in range(w):
			render_sprite(base, j*8, i*8)
			base += 16

def color_bytes(start_x, w, h):
	base = 0
	for i in range(h):
		for j in range(w):
			col = (0, 0, 0)
			d = get_byte(base)
			base += 1

			if d == 0:
				col = (255, 0, 0)
			elif d == -1:
				col = (0, 0, 0)
			elif d >= ord(' ') and d <= ord('~'):
				col = (0, 255, 0)
			else:
				col = (0, 0, 255)

			put_pixel(start_x+j, i, col)

def entropy(start_x, w, h):

	base = 0
	sample = size/h

	for i in range(H):
		q = {}
		for j in range(sample):
			d = get_byte(base+j)
			q[d] = 1

		base += sample

		ent = (float(len(q)) / sample)

		for j in range(w):
			Z = int(ent * 255)
			put_pixel(start_x+j, i, (Z, Z, Z))

render_sprite_sheet(tiles_per_row, H/8)
color_bytes(tiles_width, row, H)
entropy(tiles_width+row, 64, H)

img.save(cart_name+'.png')
print('saved image.')

