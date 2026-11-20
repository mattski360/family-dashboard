"""5th-grade multiple-choice bank for earning extra Cougar Run / Cougar Dash time.
Each item: id, subject (math|science|social|english), q, choices (4), answer (exact choice text), explain.
"""
# Answers are stored as the correct choice text so shuffled options stay unambiguous.

Q = []

def add(subject, q, choices, answer, explain, qid=None):
    assert answer in choices, (q, answer, choices)
    assert len(choices) == 4, q
    assert len(set(choices)) == 4, q
    prefix = {"math":"m","science":"sci","social":"soc","english":"e"}[subject]
    Q.append({
        "id": qid or f"{prefix}{len([x for x in Q if x['subject']==subject])+1:03d}",
        "subject": subject,
        "q": q,
        "choices": choices,
        "answer": answer,
        "explain": explain,
    })

# ========================= MATH =========================
# Fractions
add("math", "What is 1/2 + 1/4?",
    ["1/4", "3/4", "2/4", "1/6"], "3/4",
    "Use a common denominator of 4: 1/2 is 2/4, and 2/4 + 1/4 = 3/4.")
add("math", "Which fraction is equivalent to 2/3?",
    ["2/4", "3/5", "4/6", "3/6"], "4/6",
    "Multiply the top and bottom of 2/3 by 2 to get 4/6.")
add("math", "What is 3/8 + 2/8?",
    ["5/8", "5/16", "1/8", "6/8"], "5/8",
    "The denominators are already the same, so add the numerators: 3 + 2 = 5. That's 5/8.")
add("math", "Which fraction is greater, 3/5 or 2/5?",
    ["2/5", "They are equal", "3/5", "You cannot tell"], "3/5",
    "When denominators are the same, the larger numerator is the larger fraction. 3/5 is greater.")
add("math", "What is 1/2 of 18?",
    ["8", "9", "6", "36"], "9",
    "Half of 18 is 9, because 18 ÷ 2 = 9.")
add("math", "Simplify 6/8.",
    ["3/4", "2/3", "6/4", "3/8"], "3/4",
    "Divide the numerator and the denominator by 2: 6 ÷ 2 = 3 and 8 ÷ 2 = 4, so 6/8 = 3/4.")
add("math", "What is 5/6 − 1/6, in simplest form?",
    ["4/6", "4/0", "2/3", "1/3"], "2/3",
    "5/6 − 1/6 = 4/6, and 4/6 simplifies to 2/3.")
add("math", "A pizza is cut into 8 equal slices. You eat 3 slices. What fraction of the pizza is left?",
    ["3/8", "5/8", "3/5", "8/3"], "5/8",
    "8 − 3 = 5 slices left, so 5 out of 8, or 5/8, remains.")
add("math", "Which fraction is equal to 1/2?",
    ["2/5", "3/8", "5/10", "1/4"], "5/10",
    "5/10 can be simplified by dividing the top and bottom by 5, which gives 1/2.")
add("math", "What is 2/5 + 1/5?",
    ["3/5", "3/10", "2/10", "1/5"], "3/5",
    "The denominators match, so add the numerators: 2 + 1 = 3. That's 3/5.")
add("math", "What is 7/4 written as a mixed number?",
    ["1 3/4", "3 1/4", "1 1/4", "2 3/4"], "1 3/4",
    "4 goes into 7 once, with 3 left over, so 7/4 = 1 3/4.")
add("math", "What is 4/4 as a whole number?",
    ["0", "4", "1", "8"], "1",
    "When the numerator and denominator are the same, the fraction equals 1.")
add("math", "What is 2/3 of 12?",
    ["4", "6", "8", "18"], "8",
    "First find 1/3 of 12, which is 4. Then 2/3 is two of those, so 8.")
add("math", "Which is greater, 3/4 or 3/8?",
    ["3/8", "3/4", "They are equal", "You cannot tell"], "3/4",
    "Write 3/4 as 6/8. 6/8 is greater than 3/8, so 3/4 is greater.")
add("math", "What is 1 − 1/4?",
    ["1/4", "3/4", "4/4", "1/3"], "3/4",
    "1 is the same as 4/4, and 4/4 − 1/4 = 3/4.")

# Decimals
add("math", "What is 0.7 written as a fraction?",
    ["7/100", "7/10", "1/7", "70/10"], "7/10",
    "The first digit after the decimal point is the tenths place, so 0.7 = 7/10.")
add("math", "What is 0.25 + 0.25?",
    ["0.4", "0.50", "0.2525", "1.00"], "0.50",
    "25 hundredths plus 25 hundredths is 50 hundredths, which is 0.50 (or 0.5).")
add("math", "Which decimal is greater, 0.8 or 0.75?",
    ["0.75", "0.8", "They are equal", "You cannot tell"], "0.8",
    "0.8 is 80 hundredths, and 0.75 is 75 hundredths. 80 hundredths is greater.")
add("math", "What is 1.5 + 2.5?",
    ["3.0", "4.0", "4.10", "3.10"], "4.0",
    "1.5 + 2.5 = 4.0, or just 4.")
add("math", "In the number 3.46, which digit is in the tenths place?",
    ["3", "4", "6", "46"], "4",
    "Just after the decimal point is the tenths place, so the 4 is in the tenths place.")
add("math", "0.4 is the same as which fraction?",
    ["4/100", "1/4", "4/10", "40/10"], "4/10",
    "0.4 means 4 tenths, which is the fraction 4/10 (and that also equals 2/5).")
add("math", "What is $3.25 + $1.50?",
    ["$4.75", "$4.25", "$5.75", "$3.75"], "$4.75",
    "Add the dollars: 3 + 1 = 4. Add the cents: 25 + 50 = 75. That's $4.75.")
add("math", "The number 0.09 is the same as:",
    ["9 tenths", "9 hundredths", "9 ones", "9 thousandths"], "9 hundredths",
    "The second digit after the decimal point is the hundredths place, so 0.09 is 9 hundredths.")
add("math", "Which decimal is the smallest?",
    ["0.3", "0.03", "0.33", "0.30"], "0.03",
    "0.03 is only 3 hundredths. 0.3 and 0.30 are both 30 hundredths, and 0.33 is 33 hundredths.")
add("math", "What is 2.4 × 10?",
    ["2.40", "24", "0.24", "240"], "24",
    "Multiplying by 10 moves the decimal point one place to the right, so 2.4 becomes 24.")

# Multiplication and division
add("math", "What is 7 × 8?",
    ["54", "56", "63", "48"], "56",
    "7 × 8 = 56. That's a multiplication fact worth knowing by heart.")
add("math", "What is 6 × 9?",
    ["54", "56", "45", "63"], "54",
    "6 × 9 = 54, and 9 × 6 is the same product.")
add("math", "What is 12 × 11?",
    ["121", "132", "144", "122"], "132",
    "12 × 10 = 120, then add one more 12 to get 132.")
add("math", "What is 81 ÷ 9?",
    ["8", "9", "7", "11"], "9",
    "9 × 9 = 81, so 81 ÷ 9 = 9.")
add("math", "What is 56 ÷ 7?",
    ["7", "8", "9", "6"], "8",
    "7 × 8 = 56, so 56 ÷ 7 = 8.")
add("math", "What is 15 × 6?",
    ["80", "90", "75", "96"], "90",
    "10 × 6 = 60 and 5 × 6 = 30. 60 + 30 = 90.")
add("math", "What is 100 ÷ 4?",
    ["20", "25", "40", "16"], "25",
    "4 × 25 = 100, so 100 ÷ 4 = 25.")
add("math", "What is 13 × 4?",
    ["42", "48", "52", "56"], "52",
    "10 × 4 = 40 and 3 × 4 = 12. 40 + 12 = 52.")
add("math", "What is 72 ÷ 8?",
    ["8", "9", "7", "6"], "9",
    "8 × 9 = 72, so 72 ÷ 8 = 9.")
add("math", "A box holds 6 rows of 8 crayons. How many crayons are in the box?",
    ["14", "42", "48", "54"], "48",
    "This is 6 groups of 8, so multiply: 6 × 8 = 48.")
add("math", "What is 145 ÷ 5?",
    ["25", "29", "35", "28"], "29",
    "5 × 29 = 145, so 145 ÷ 5 = 29.")
add("math", "What is 24 × 5?",
    ["100", "110", "120", "125"], "120",
    "24 × 5 is the same as 24 × 10 ÷ 2, or 20 × 5 = 100 plus 4 × 5 = 20, which is 120.")
add("math", "What is 9 × 9?",
    ["72", "81", "99", "18"], "81",
    "9 × 9 = 81.")
add("math", "What is 64 ÷ 4?",
    ["12", "14", "16", "18"], "16",
    "4 × 16 = 64, so 64 ÷ 4 = 16.")
add("math", "What is the remainder when 17 is divided by 5?",
    ["0", "1", "2", "3"], "2",
    "5 × 3 = 15, and 17 − 15 = 2, so 17 ÷ 5 is 3 remainder 2.")

# Area, perimeter, volume
add("math", "What is the area of a rectangle that is 6 units long and 4 units wide?",
    ["10 square units", "20 square units", "24 square units", "64 square units"], "24 square units",
    "Area of a rectangle is length × width: 6 × 4 = 24 square units.")
add("math", "What is the perimeter of a rectangle that is 6 units long and 4 units wide?",
    ["10 units", "20 units", "24 units", "16 units"], "20 units",
    "Perimeter is the distance around: 6 + 4 + 6 + 4 = 20, or 2 × (6 + 4) = 20.")
add("math", "What is the volume of a rectangular box that is 3 units by 2 units by 4 units?",
    ["9 cubic units", "12 cubic units", "24 cubic units", "18 cubic units"], "24 cubic units",
    "Volume is length × width × height: 3 × 2 × 4 = 24 cubic units.")
add("math", "What is the area of a square with sides of 9 units?",
    ["18 square units", "36 square units", "81 square units", "72 square units"], "81 square units",
    "Area of a square is side × side: 9 × 9 = 81 square units.")
add("math", "What is the perimeter of a square with sides of 7 units?",
    ["14 units", "21 units", "28 units", "49 units"], "28 units",
    "A square has 4 equal sides, so the perimeter is 7 × 4 = 28 units.")
add("math", "A rectangular prism is 5 cm long, 2 cm wide, and 3 cm high. What is its volume?",
    ["10 cubic cm", "15 cubic cm", "30 cubic cm", "11 cubic cm"], "30 cubic cm",
    "Volume = length × width × height: 5 × 2 × 3 = 30 cubic centimeters.")
add("math", "A rectangle has an area of 36 square units and a length of 9 units. What is its width?",
    ["4 units", "6 units", "27 units", "45 units"], "4 units",
    "Area = length × width, so 36 = 9 × width. 36 ÷ 9 = 4, so the width is 4 units.")

# Order of operations and place value
add("math", "What is 3 + 4 × 2?",
    ["14", "11", "10", "7"], "11",
    "Multiply first, then add: 4 × 2 = 8, and 3 + 8 = 11. (Parentheses would be needed to add first.)")
add("math", "What is (3 + 4) × 2?",
    ["11", "14", "10", "7"], "14",
    "Parentheses first: 3 + 4 = 7, then 7 × 2 = 14.")
add("math", "What is 10 − 3 × 2?",
    ["14", "7", "4", "6"], "4",
    "Multiply first: 3 × 2 = 6, then 10 − 6 = 4.")
add("math", "What is 8 ÷ 2 + 6?",
    ["1", "8", "10", "16"], "10",
    "Divide first: 8 ÷ 2 = 4, then 4 + 6 = 10.")
add("math", "What is 5 × (6 − 2)?",
    ["28", "20", "13", "8"], "20",
    "Parentheses first: 6 − 2 = 4, then 5 × 4 = 20.")
add("math", "What is 18 ÷ (3 + 3)?",
    ["9", "6", "3", "4"], "3",
    "Parentheses first: 3 + 3 = 6, then 18 ÷ 6 = 3.")
add("math", "What is 2 + 3 × 5 − 1?",
    ["24", "16", "14", "11"], "16",
    "Multiply first: 3 × 5 = 15. Then 2 + 15 − 1 = 16.")
add("math", "In the number 3,752, what is the value of the digit 7?",
    ["7", "70", "700", "7,000"], "700",
    "The 7 is in the hundreds place, so its value is 700.")
add("math", "How many thousands are in 1,000,000?",
    ["10", "100", "1,000", "10,000"], "1,000",
    "1,000,000 is one million, and 1,000 × 1,000 = 1,000,000, so there are 1,000 thousands.")
add("math", "What is 4,000 + 200 + 5?",
    ["4,205", "4,250", "425", "4,025"], "4,205",
    "4,000 + 200 = 4,200, plus 5 is 4,205.")

# ========================= SCIENCE =========================
add("science", "When liquid water freezes, it changes into which state of matter?",
    ["Gas", "Solid", "Plasma", "Vapor"], "Solid",
    "Freezing turns a liquid into a solid. Frozen water is ice.")
add("science", "When ice melts, it changes from a solid into a:",
    ["Gas", "Liquid", "Crystal", "Cloud"], "Liquid",
    "Melting turns a solid into a liquid. Melted ice is liquid water.")
add("science", "When a puddle dries up in the sun, the water is becoming a gas. This is called:",
    ["Condensation", "Freezing", "Evaporation", "Precipitation"], "Evaporation",
    "Evaporation is when a liquid changes into a gas, often because of heat from the sun.")
add("science", "Water vapor cooling and turning back into liquid water is called:",
    ["Evaporation", "Melting", "Condensation", "Sublimation"], "Condensation",
    "Condensation is the change from a gas to a liquid. That's how clouds and dew form.")
add("science", "Which state of matter has a definite shape and a definite volume?",
    ["Solid", "Liquid", "Gas", "Vapor"], "Solid",
    "A solid keeps its own shape and volume. A liquid has a definite volume but takes the shape of its container.")
add("science", "Which state of matter takes the shape of its container but has a definite volume?",
    ["Solid", "Liquid", "Gas", "Steam"], "Liquid",
    "A liquid has a definite volume (it doesn't fill the whole room) but it takes the shape of its container.")
add("science", "Water in the gas state is often called:",
    ["Ice", "Rain", "Water vapor", "Hail"], "Water vapor",
    "Water vapor is water as a gas. You can't usually see it in the air around you.")
add("science", "Rain, snow, sleet, and hail are all types of:",
    ["Evaporation", "Condensation", "Precipitation", "Erosion"], "Precipitation",
    "Precipitation is water that falls from clouds. It can be rain, snow, sleet, or hail.")
add("science", "Clouds form when water vapor in the air:",
    ["Freezes into soil", "Condenses into tiny water droplets", "Turns into oxygen", "Burns up"], "Condenses into tiny water droplets",
    "Cool air makes water vapor condense into tiny droplets or ice crystals, and those make a cloud.")
add("science", "The water cycle is the path water takes as it:",
    ["Stays only in rivers", "Moves between Earth and the air over and over", "Leaves Earth forever", "Turns into metal"], "Moves between Earth and the air over and over",
    "Water evaporates, condenses into clouds, falls as precipitation, and then the cycle starts again.")
add("science", "In a food chain, plants that make their own food are called:",
    ["Consumers", "Producers", "Decomposers", "Predators"], "Producers",
    "Producers, usually plants, make their own food using sunlight. Other living things depend on them.")
add("science", "An animal that eats only plants is a:",
    ["Carnivore", "Herbivore", "Omnivore", "Decomposer"], "Herbivore",
    "Herbivores eat plants. Cows, deer, and rabbits are herbivores.")
add("science", "An animal that eats only other animals is a:",
    ["Herbivore", "Carnivore", "Producer", "Omnivore"], "Carnivore",
    "Carnivores eat meat. A lion or a hawk is a carnivore.")
add("science", "An animal that eats both plants and animals is an:",
    ["Herbivore", "Carnivore", "Omnivore", "Producer"], "Omnivore",
    "Omnivores eat both plants and animals. People and bears are omnivores.")
add("science", "Fungi and bacteria that break down dead plants and animals are called:",
    ["Producers", "Predators", "Decomposers", "Herbivores"], "Decomposers",
    "Decomposers recycle nutrients back into the soil by breaking down dead things.")
add("science", "A food chain usually starts with energy from:",
    ["The moon", "The sun", "The wind", "A cave"], "The sun",
    "The sun's energy is captured by plants, and then it moves to the animals that eat them.")
add("science", "The place where an organism lives is its:",
    ["Population", "Habitat", "Fossil", "Cell"], "Habitat",
    "A habitat is an organism's home — the place that gives it food, water, and shelter.")
add("science", "A group of the same kind of living thing in the same area is a:",
    ["Habitat", "Population", "Climate", "Cell"], "Population",
    "A population is all the members of one species living in the same place, like all the trout in a lake.")
add("science", "All the living and nonliving things in an area together make up an:",
    ["Island", "Ecosystem", "Organ", "Orbit"], "Ecosystem",
    "An ecosystem includes plants, animals, water, soil, air, and how they all interact.")
add("science", "An animal that hunts other animals for food is a:",
    ["Producer", "Prey", "Predator", "Decomposer"], "Predator",
    "A predator hunts prey. A fox hunting a rabbit is a predator-prey relationship.")
add("science", "Earth spinning on its axis once every 24 hours causes:",
    ["The seasons", "Day and night", "A year", "High tide only"], "Day and night",
    "Earth's rotation makes the sun appear to rise and set, giving us day and night.")
add("science", "Earth traveling all the way around the sun once is called a:",
    ["Rotation", "Revolution", "Eclipse", "Phase"], "Revolution",
    "One revolution around the sun takes about 365 days, which is one year.")
add("science", "The moon takes about a month to:",
    ["Burn out", "Orbit Earth", "Become a star", "Fall into the sun"], "Orbit Earth",
    "The moon revolves around Earth in a little less than a month, and that's why we see changing phases.")
add("science", "The sun is a:",
    ["Planet", "Moon", "Star", "Comet"], "Star",
    "The sun is the star at the center of our solar system. It gives Earth light and heat.")
add("science", "How many planets are in our solar system?",
    ["7", "8", "9", "10"], "8",
    "There are 8 planets. Pluto is now classified as a dwarf planet.")
add("science", "Which planet is closest to the sun?",
    ["Venus", "Earth", "Mercury", "Mars"], "Mercury",
    "Mercury is the first planet from the sun, so it is the closest.")
add("science", "Which planet is the largest in our solar system?",
    ["Earth", "Saturn", "Jupiter", "Neptune"], "Jupiter",
    "Jupiter is a huge gas giant — the largest planet in our solar system.")
add("science", "Earth has seasons mainly because:",
    ["The sun turns off in winter", "Earth's axis is tilted as it revolves around the sun", "The moon blocks the sun", "Earth is closer to the moon in summer"], "Earth's axis is tilted as it revolves around the sun",
    "The tilt means one hemisphere gets more direct sunlight at some times of the year, and that makes seasons.")
add("science", "Earth is which planet from the sun?",
    ["The first", "The second", "The third", "The fourth"], "The third",
    "The order is Mercury, Venus, Earth, Mars. Earth is third.")
add("science", "A fossil is:",
    ["A type of cloud", "The remains or traces of a once-living thing", "A living insect", "A kind of metal tool"], "The remains or traces of a once-living thing",
    "Fossils are clues about plants and animals that lived long ago, often preserved in rock.")
add("science", "What is the difference between weather and climate?",
    ["They mean exactly the same thing", "Weather is day-to-day, climate is the average weather over many years", "Climate happens only at night", "Weather is only rain"], "Weather is day-to-day, climate is the average weather over many years",
    "Weather is what's happening today. Climate is the typical pattern of weather in a place over a long time.")
add("science", "The layer of Earth that we live on is the:",
    ["Core", "Mantle", "Crust", "Atmosphere only"], "Crust",
    "The crust is Earth's thin outer layer of rock. Under it are the mantle and the core.")
add("science", "The very center of Earth is called the:",
    ["Crust", "Mantle", "Core", "Horizon"], "Core",
    "Earth's core is at the center. It has a liquid outer core and a solid inner core.")
add("science", "Which organ pumps blood through the body?",
    ["Lungs", "Heart", "Stomach", "Brain"], "Heart",
    "The heart is a muscle that pumps blood. That's the circulatory system.")
add("science", "Which organs take in oxygen when you breathe?",
    ["Kidneys", "Lungs", "Bones", "Stomach"], "Lungs",
    "Your lungs are part of the respiratory system. They take in oxygen and help you get rid of carbon dioxide.")
add("science", "Which organ is the body's control center?",
    ["Heart", "Liver", "Brain", "Skin"], "Brain",
    "The brain, part of the nervous system, controls thoughts, movement, and many body functions.")
add("science", "The bones of the body make up the:",
    ["Muscular system", "Skeletal system", "Digestive system", "Respiratory system"], "Skeletal system",
    "The skeletal system is all of your bones. It supports the body and protects organs.")
add("science", "The smallest unit of life is the:",
    ["Organ", "Tissue", "Cell", "Organism"], "Cell",
    "All living things are made of cells. Cells are the building blocks of life.")
add("science", "Which organs filter waste from the blood and make urine?",
    ["Lungs", "Kidneys", "Bones", "Ears"], "Kidneys",
    "The kidneys clean the blood and make urine, which leaves the body as waste.")
add("science", "What is the body's largest organ?",
    ["Heart", "Brain", "Skin", "Liver"], "Skin",
    "Skin covers the whole body, so it is the largest organ. It helps protect you and control temperature.")
add("science", "When you breathe, you take in oxygen and breathe out:",
    ["Only water", "Carbon dioxide", "Nitrogen metal", "Helium"], "Carbon dioxide",
    "Your cells use oxygen and make carbon dioxide as a waste gas, which you exhale.")
add("science", "Muscles are important because they:",
    ["Store only fat", "Help you move", "Pump only air into bones", "Make sunlight"], "Help you move",
    "The muscular system works with the skeleton so you can walk, lift, and even smile.")

# ========================= SOCIAL STUDIES =========================
add("social", "What is the capital of the United States?",
    ["New York City", "Washington, D.C.", "Philadelphia", "Boston"], "Washington, D.C.",
    "Washington, D.C. is the U.S. capital, where the President and Congress work.")
add("social", "How many states are in the United States?",
    ["13", "48", "50", "52"], "50",
    "There are 50 states. The 13 original colonies came first, and more states were added later.")
add("social", "Who was the first President of the United States?",
    ["Thomas Jefferson", "Abraham Lincoln", "George Washington", "Benjamin Franklin"], "George Washington",
    "George Washington was the first U.S. President and is often called the Father of His Country.")
add("social", "In what year was the Declaration of Independence adopted?",
    ["1492", "1776", "1787", "1812"], "1776",
    "The Declaration of Independence was adopted on July 4, 1776.")
add("social", "How many branches of government does the United States have?",
    ["Two", "Three", "Four", "Five"], "Three",
    "The three branches are legislative, executive, and judicial. They share power so no branch becomes too strong.")
add("social", "Which branch of government makes the laws?",
    ["Executive", "Judicial", "Legislative", "Military"], "Legislative",
    "The legislative branch is Congress, which is the Senate and the House of Representatives.")
add("social", "Which branch of government carries out, or enforces, the laws?",
    ["Legislative", "Executive", "Judicial", "State courts only"], "Executive",
    "The executive branch is headed by the President, who carries out the laws.")
add("social", "Which branch of government interprets the laws?",
    ["Legislative", "Executive", "Judicial", "The Cabinet"], "Judicial",
    "The judicial branch, including the Supreme Court, interprets laws and the Constitution.")
add("social", "The first 10 amendments to the Constitution are called the:",
    ["Mayflower Compact", "Bill of Rights", "Emancipation Proclamation", "Gettysburg Address"], "Bill of Rights",
    "The Bill of Rights lists important freedoms, such as freedom of speech and religion.")
add("social", "How many senators does each U.S. state have in Congress?",
    ["1", "2", "3", "It depends on the state's population"], "2",
    "Every state has 2 senators, so all states are equal in the Senate.")
add("social", "A U.S. President is elected to a term of how many years?",
    ["2 years", "4 years", "6 years", "8 years"], "4 years",
    "A presidential term is 4 years. A president may be elected to at most two terms.")
add("social", "The 13 stripes on the U.S. flag stand for:",
    ["13 presidents", "The 13 original colonies", "13 amendments", "13 rivers"], "The 13 original colonies",
    "The 13 stripes honor the 13 colonies that first formed the United States.")
add("social", "The stars on the U.S. flag stand for:",
    ["The 13 colonies", "The 50 states", "The Supreme Court justices", "The months of the year"], "The 50 states",
    "There is one star for each of the 50 states.")
add("social", "On what date do Americans celebrate Independence Day?",
    ["May 1", "July 4", "November 11", "December 25"], "July 4",
    "Independence Day is July 4, the anniversary of the Declaration of Independence in 1776.")
add("social", "Which ocean is on the East Coast of the United States?",
    ["Pacific Ocean", "Atlantic Ocean", "Indian Ocean", "Arctic Ocean"], "Atlantic Ocean",
    "The Atlantic Ocean is on the East Coast. The Pacific Ocean is on the West Coast.")
add("social", "Which ocean is on the West Coast of the United States?",
    ["Atlantic Ocean", "Pacific Ocean", "Indian Ocean", "Southern Ocean"], "Pacific Ocean",
    "The Pacific Ocean borders states like Washington, Oregon, and Hawaii.")
add("social", "The Statue of Liberty stands in the harbor of which city?",
    ["Boston", "New York", "Chicago", "Miami"], "New York",
    "The Statue of Liberty is in New York Harbor. It was a gift from France.")
add("social", "What is the highest court in the United States?",
    ["The Senate", "The Supreme Court", "The Cabinet", "State court"], "The Supreme Court",
    "The Supreme Court is the highest court in the judicial branch.")
add("social", "Who was the main author of the Declaration of Independence?",
    ["George Washington", "Benjamin Franklin", "Thomas Jefferson", "John Adams"], "Thomas Jefferson",
    "Thomas Jefferson wrote the first draft and is remembered as the main author.")
add("social", "In what year was the U.S. Constitution written?",
    ["1776", "1787", "1812", "1865"], "1787",
    "Delegates wrote the Constitution at the Constitutional Convention in 1787.")
add("social", "The First Amendment protects freedom of speech, religion, and the:",
    ["Right to be king", "Press", "Right to own the moon", "Right to skip school"], "Press",
    "The First Amendment also protects freedom of the press, assembly, and petition.")
add("social", "The United States is on which continent?",
    ["Europe", "Africa", "North America", "Asia"], "North America",
    "The United States is in North America, along with countries such as Canada and Mexico.")
add("social", "How many continents are there on Earth?",
    ["5", "6", "7", "8"], "7",
    "The seven continents are Africa, Antarctica, Asia, Australia, Europe, North America, and South America.")
add("social", "On most maps, which direction is at the top?",
    ["South", "East", "North", "West"], "North",
    "Maps usually have north at the top. A compass rose shows the directions.")
add("social", "What is the capital of Utah?",
    ["Provo", "Ogden", "Salt Lake City", "St. George"], "Salt Lake City",
    "Salt Lake City is Utah's capital and its largest city.")
add("social", "Utah's nickname is the:",
    ["Sunshine State", "Beehive State", "Lone Star State", "Evergreen State"], "Beehive State",
    "Utah is the Beehive State. A beehive stands for hard work and industry.")
add("social", "In what year did Utah become a state?",
    ["1776", "1847", "1896", "1912"], "1896",
    "Utah became a state on January 4, 1896.")
add("social", "Utah was the 45th state. That means how many states joined the country before Utah?",
    ["44", "45", "46", "50"], "44",
    "If Utah is the 45th state, then 44 states were admitted before it.")
add("social", "The Great Salt Lake is known for being:",
    ["A freshwater lake with no salt", "Much saltier than the ocean", "An ocean on the East Coast", "A man-made swimming pool only"], "Much saltier than the ocean",
    "The Great Salt Lake is so salty that people can float in it easily.")
add("social", "Which of these is a national park in Utah?",
    ["Yellowstone", "Zion", "Everglades", "Acadia"], "Zion",
    "Zion is one of Utah's five national parks. The others are Arches, Bryce Canyon, Canyonlands, and Capitol Reef.")
add("social", "What is Utah's state flower?",
    ["Rose", "Sego lily", "Sunflower", "Tulip"], "Sego lily",
    "The sego lily is Utah's state flower. It is a white, cup-shaped wildflower.")
add("social", "What is Utah's official state tree?",
    ["Pine", "Oak", "Quaking aspen", "Maple"], "Quaking aspen",
    "The quaking aspen is Utah's state tree. Its leaves shimmer, or 'quake,' in the wind.")
add("social", "What is Utah's state motto?",
    ["Live Free or Die", "Industry", "Eureka", "Hope"], "Industry",
    "Utah's motto is Industry, which means hard work — just like the beehive symbol.")
add("social", "The Wasatch Range is a:",
    ["River in Texas", "Mountain range in Utah", "Desert in Nevada", "Lake in Florida"], "Mountain range in Utah",
    "The Wasatch Range runs along the western edge of the Rocky Mountains in Utah.")
add("social", "What is the highest peak in Utah?",
    ["Mount Everest", "Kings Peak", "Pikes Peak", "Mount Whitney"], "Kings Peak",
    "Kings Peak, in the Uinta Mountains, is the highest point in Utah.")
add("social", "Delicate Arch is a famous landmark in which Utah national park?",
    ["Zion", "Bryce Canyon", "Arches", "Capitol Reef"], "Arches",
    "Delicate Arch is in Arches National Park, near Moab.")
add("social", "Four Corners is the only place in the United States where how many states meet?",
    ["Two", "Three", "Four", "Five"], "Four",
    "Utah, Colorado, New Mexico, and Arizona all meet at Four Corners.")
add("social", "Utah celebrates Pioneer Day on:",
    ["July 4", "July 24", "January 4", "December 24"], "July 24",
    "Pioneer Day, July 24, remembers the 1847 arrival of pioneers in the Salt Lake Valley.")
add("social", "Utah's state insect is the:",
    ["Butterfly", "Honeybee", "Ladybug", "Dragonfly"], "Honeybee",
    "The honeybee is a good fit for the Beehive State and its motto, Industry.")
add("social", "Utah has how many national parks?",
    ["Two", "Three", "Five", "Ten"], "Five",
    "Utah's five national parks are Zion, Bryce Canyon, Capitol Reef, Arches, and Canyonlands.")

# ========================= ENGLISH =========================
add("english", "A word that names a person, place, thing, or idea is a:",
    ["Verb", "Noun", "Adjective", "Adverb"], "Noun",
    "Nouns name people, places, things, or ideas, such as teacher, park, ball, or honesty.")
add("english", "A word that shows action, like jump or write, is a:",
    ["Noun", "Verb", "Adjective", "Pronoun"], "Verb",
    "A verb shows an action or a state of being. Run, think, and is are all verbs.")
add("english", "A word that describes a noun, like happy or blue, is an:",
    ["Adverb", "Adjective", "Verb", "Conjunction"], "Adjective",
    "Adjectives describe nouns. In 'the blue bike,' blue is an adjective.")
add("english", "A word that describes a verb, often ending in -ly, is an:",
    ["Adjective", "Adverb", "Noun", "Pronoun"], "Adverb",
    "Adverbs describe verbs, adjectives, or other adverbs. In 'she ran quickly,' quickly is an adverb.")
add("english", "A word that takes the place of a noun, like he, she, or they, is a:",
    ["Adjective", "Verb", "Pronoun", "Preposition"], "Pronoun",
    "Pronouns stand in for nouns so we don't have to repeat the same name over and over.")
add("english", "Which word correctly completes the sentence: 'The students put _____ books in their backpacks.'?",
    ["there", "their", "they're", "they"], "their",
    "Their shows possession — the books belong to the students. They're means they are, and there is a place.")
add("english", "Which word means 'they are'?",
    ["Their", "There", "They're", "They"], "They're",
    "They're is a contraction of they are. Their shows ownership, and there is a place.")
add("english", "Which sentence uses 'there' correctly?",
    ["There going to the store.", "The dog wagged there tail.", "Please sit over there.", "There books are new."], "Please sit over there.",
    "There points to a place. In this sentence, it tells where to sit.")
add("english", "Which word is a contraction for 'you are'?",
    ["Your", "You're", "Yore", "Youre'"], "You're",
    "You're = you are. Your shows possession, as in 'your coat.'")
add("english", "Which sentence uses 'it's' correctly?",
    ["The cat licked it's paws.", "It's time for lunch.", "The dog lost it's bone.", "The tree dropped it's leaves."], "It's time for lunch.",
    "It's means it is or it has. The possessive form, with no apostrophe, is its, as in 'its paws.'")
add("english", "A complete sentence must have a subject and a:",
    ["Comma", "Predicate (verb)", "Question mark", "Capital letter only"], "Predicate (verb)",
    "A complete sentence needs a subject (who or what) and a predicate that includes a verb.")
add("english", "What is the contraction for 'do not'?",
    ["dont", "doesn't", "don't", "didn't"], "don't",
    "Don't is do + not. The apostrophe takes the place of the missing o.")
add("english", "Which sentence uses commas in a list correctly?",
    ["I bought apples oranges and bananas.", "I bought apples, oranges, and bananas.", "I bought, apples oranges and, bananas.", "I bought apples oranges, and, bananas."], "I bought apples, oranges, and bananas.",
    "Use commas to separate items in a list: apples, oranges, and bananas.")
add("english", "Which word should always be capitalized?",
    ["mountain", "city", "utah", "river"], "utah",
    "Utah is a proper noun — the name of a specific place — so it is capitalized.")
add("english", "What is the past tense of the verb run?",
    ["Runned", "Ran", "Running", "Runs"], "Ran",
    "Run is irregular. We say 'yesterday I ran,' not 'runned.'")
add("english", "What is the plural of child?",
    ["Childs", "Childes", "Children", "Childrens"], "Children",
    "Child has an irregular plural: children.")
add("english", "Which of these is a complete sentence?",
    ["After the game.", "The cougar jumped over the rock.", "Running down the trail.", "Because it was snowing."], "The cougar jumped over the rock.",
    "This sentence has a subject (the cougar) and a verb (jumped). The others are fragments.")
add("english", "A synonym is a word that:",
    ["Means the opposite", "Means almost the same thing", "Rhymes", "Is always a noun"], "Means almost the same thing",
    "Synonyms are words with the same or nearly the same meaning, like happy and glad.")
add("english", "Which word is a synonym for happy?",
    ["Angry", "Glad", "Tired", "Hungry"], "Glad",
    "Glad means almost the same as happy. Angry is closer to an antonym.")
add("english", "An antonym is a word that:",
    ["Means the same thing", "Means the opposite", "Sounds the same", "Has a prefix"], "Means the opposite",
    "Antonyms are opposites, like hot and cold or up and down.")
add("english", "Which word is an antonym of hot?",
    ["Warm", "Cold", "Spicy", "Sunny"], "Cold",
    "Cold is the opposite of hot. Warm is closer in meaning, not opposite.")
add("english", "The prefix un- in unhappy means:",
    ["Again", "Not", "Full of", "Before"], "Not",
    "Un- often means not. Unhappy means not happy.")
add("english", "The prefix re- in rebuild means:",
    ["Not", "Again", "Wrongly", "Without"], "Again",
    "Re- often means again. Rebuild means to build again.")
add("english", "The suffix -less in hopeless means:",
    ["Full of", "Without", "More", "Again"], "Without",
    "The suffix -less means without. Hopeless means without hope.")
add("english", "The suffix -ful in hopeful means:",
    ["Without", "Full of", "Not", "Before"], "Full of",
    "The suffix -ful means full of. Hopeful means full of hope.")
add("english", "In the sentence 'The arid desert got almost no rain,' arid most nearly means:",
    ["Frozen", "Crowded", "Dry", "Noisy"], "Dry",
    "Context clues help: a desert that gets almost no rain is dry, so arid means dry.")
add("english", "The word bat can mean a flying animal or a piece of sports equipment. This is an example of:",
    ["A prefix", "A multiple-meaning word", "An antonym", "A contraction"], "A multiple-meaning word",
    "Some words have more than one meaning. You use context to tell which meaning is right.")
add("english", "A simile is a comparison that uses:",
    ["Only numbers", "Like or as", "No verbs", "Only capital letters"], "Like or as",
    "A simile compares two things using like or as, such as 'as brave as a lion.'")
add("english", "Which sentence is a simile?",
    ["The classroom was a zoo.", "She is as fast as a cheetah.", "The wind whispered.", "I've told you a million times."], "She is as fast as a cheetah.",
    "This comparison uses as, so it is a simile. 'The classroom was a zoo' is a metaphor.")
add("english", "A metaphor compares two things:",
    ["Using like or as", "Without using like or as", "Only if they rhyme", "Only in questions"], "Without using like or as",
    "A metaphor says one thing is another, like 'The classroom was a zoo.'")
add("english", "Which sentence is a metaphor?",
    ["He is as tall as a tree.", "The snow was a white blanket.", "The bee went buzz.", "Sally sells seashells."], "The snow was a white blanket.",
    "This says the snow was a blanket, which is a comparison without like or as.")
add("english", "Personification is when a writer:",
    ["Uses only facts", "Gives human qualities to something that is not human", "Repeats the same word", "Asks a question"], "Gives human qualities to something that is not human",
    "In 'The wind whispered,' the wind is given the human action of whispering.")
add("english", "Which sentence uses personification?",
    ["The leaves danced in the wind.", "The leaves were green.", "The tree was tall.", "I raked the leaves."], "The leaves danced in the wind.",
    "Leaves don't really dance. Giving them that human action is personification.")
add("english", "Hyperbole is:",
    ["A type of noun", "An extreme exaggeration", "A punctuation mark", "A kind of map"], "An extreme exaggeration",
    "Hyperbole is exaggeration for effect, like 'I've told you a million times.'")
add("english", "Which sentence is hyperbole?",
    ["I am a little tired.", "I've told you a million times.", "The dog barked.", "She walked to school."], "I've told you a million times.",
    "Nobody has literally said something a million times. That's exaggeration, or hyperbole.")
add("english", "Onomatopoeia is a word that:",
    ["Names a person", "Imitates a sound", "Means the opposite", "Is always capitalized"], "Imitates a sound",
    "Buzz, crash, hiss, and splash are onomatopoeia because they sound like the noises they name.")
add("english", "Which word is an example of onomatopoeia?",
    ["Beautiful", "Buzz", "Quickly", "Friendship"], "Buzz",
    "Buzz sounds like the noise a bee or a buzzer makes, so it is onomatopoeia.")
add("english", "Alliteration is the repetition of:",
    ["Ending punctuation", "The same beginning sound in nearby words", "Only long vowels", "Rhyming last words only"], "The same beginning sound in nearby words",
    "Silly snakes slither is alliteration because of the repeated s sound.")
add("english", "Which phrase is an example of alliteration?",
    ["The cat sat down.", "Silly snakes slither.", "I went home.", "The sun is hot."], "Silly snakes slither.",
    "The words start with the same s sound, which is alliteration.")
add("english", "The idiom 'it's raining cats and dogs' means:",
    ["Animals are falling from the sky", "It is raining very hard", "The weather is sunny", "Someone is allergic to pets"], "It is raining very hard",
    "An idiom has a meaning different from the literal words. This one means a heavy rain.")

# A few more to pad coverage and keep subjects even
add("math", "What is 3/4 of 20?",
    ["5", "10", "15", "16"], "15",
    "1/4 of 20 is 5, so 3/4 is 3 × 5 = 15.")
add("math", "A triangle has how many sides?",
    ["3", "4", "5", "6"], "3",
    "A triangle is a polygon with 3 sides and 3 angles.")
add("math", "How many degrees are in a right angle?",
    ["45", "90", "180", "360"], "90",
    "A right angle measures 90 degrees. It looks like the corner of a square.")
add("math", "How many degrees are in a full circle?",
    ["90", "180", "270", "360"], "360",
    "A full turn around a circle is 360 degrees.")
add("science", "What force pulls objects toward the center of Earth?",
    ["Magnetism", "Gravity", "Friction only", "Electricity"], "Gravity",
    "Gravity is the force that pulls objects toward Earth, which is why things fall down.")
add("science", "A shadow is made when an object:",
    ["Glows", "Blocks light", "Melts", "Makes sound"], "Blocks light",
    "When an object blocks light, a darker area called a shadow forms behind it.")
add("science", "Plants make food using sunlight in a process called:",
    ["Digestion", "Photosynthesis", "Evaporation", "Hibernation"], "Photosynthesis",
    "In photosynthesis, plants use sunlight, water, and carbon dioxide to make food and oxygen.")
add("social", "The President of the United States lives in the:",
    ["Capitol Building", "White House", "Supreme Court", "Liberty Bell"], "White House",
    "The White House in Washington, D.C., is the President's official home and office.")
add("social", "Memorial Day honors:",
    ["The first President only", "U.S. service members who died in war", "Teachers", "Inventors"], "U.S. service members who died in war",
    "Memorial Day is a U.S. holiday to remember those who died while serving in the military.")
add("english", "Which word is a verb in the sentence 'The kids played soccer'?",
    ["The", "kids", "played", "soccer"], "played",
    "Played is the action in the sentence, so it is the verb.")
add("english", "Which word is a noun in the sentence 'A bright moon shone'?",
    ["A", "bright", "moon", "shone"], "moon",
    "Moon names a thing, so it is a noun. Bright is an adjective, and shone is a verb.")

def validate():
    ids = [x["id"] for x in Q]
    assert len(ids) == len(set(ids)), "duplicate ids"
    qs = [x["q"] for x in Q]
    assert len(qs) == len(set(qs)), "duplicate questions"
    forbidden = ("california", "disneyland", "disney", "los angeles")
    low = "\n".join(x["q"]+" "+" ".join(x["choices"])+" "+x["answer"]+" "+x["explain"] for x in Q).lower()
    for w in forbidden:
        assert w not in low, f"forbidden term: {w}"
    for x in Q:
        assert x["answer"] in x["choices"]
        assert len(x["choices"]) == 4
        assert x["subject"] in ("math", "science", "social", "english")
        assert x["explain"].strip()
        assert len(x["q"]) > 8
    return True

if __name__ == "__main__":
    validate()
    from collections import Counter
    c = Counter(x["subject"] for x in Q)
    print("count", len(Q), dict(c))
    import json, pathlib
    out = pathlib.Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(Q, ensure_ascii=False, indent=2) + "\n")
    print("wrote", out)
