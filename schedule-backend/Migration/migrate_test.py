import pandas as pd
import re

def make_unique_course_id(abreviatura, docente_id):
    abreviatura = abreviatura.replace(" ", "_")
    teacher = int(docente_id) if pd.notna(docente_id) else "XXX"
    return f"{abreviatura}_t{teacher}"


def csv_to_ctt_courses_section(csv_path, capacity_default=30):
    df = pd.read_csv(csv_path)

    required_cols = {"abreviatura", "docente_id"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {', '.join(required_cols)}")

    t_pattern = re.compile(r'-T\.?\d+')
    t_counts = df.groupby('abreviatura')['abreviatura'].apply(
        lambda x: x.apply(lambda v: bool(t_pattern.search(str(v)))).sum()
    ).to_dict()

    courses_lines = ["COURSES:"]

    grouped = df.groupby(['abreviatura', 'docente_id'])

    for (abreviatura, docente_id), group_df in grouped:
        teacher = int(docente_id) if pd.notna(docente_id) else "XXX"
        count_for_pair = len(group_df)
        num_T_for_abreviatura = t_counts.get(abreviatura.replace(" ", "_"), 0)

        unique_id = make_unique_course_id(abreviatura, docente_id)

        line = f"{unique_id} t{teacher} {count_for_pair} {num_T_for_abreviatura} {capacity_default}"
        courses_lines.append(line)

    return "\n".join(courses_lines), grouped


def csv_to_ctt_rooms_section(csv_path, abreviatura_col='abreviatura', capacidade_col='capacidade'):
    df = pd.read_csv(csv_path)

    if not {abreviatura_col, capacidade_col}.issubset(df.columns):
        raise ValueError(f"CSV must contain columns '{abreviatura_col}' and '{capacidade_col}'")

    rooms_lines = ["ROOMS:"]
    for _, row in df.iterrows():
        room_name = str(row[abreviatura_col]).strip().replace(" ", "_")
        capacity = int(row[capacidade_col])
        rooms_lines.append(f"{room_name} {capacity}")

    return "\n".join(rooms_lines), len(df)


def generate_curricula(blocos_path, cadeiras_bloco_path, cursos_path):
    blocos_df = pd.read_csv(blocos_path)
    cadeiras_bloco_df = pd.read_csv(cadeiras_bloco_path)
    cursos_df = pd.read_csv(cursos_path)

    merged = cadeiras_bloco_df.merge(
        cursos_df[['id', 'abreviatura', 'docente_id']],
        left_on='cadeira_id',
        right_on='id',
        how='left'
    )

    merged = merged.merge(
        blocos_df[['id', 'abreviatura']],
        left_on='bloco_id',
        right_on='id',
        suffixes=('_cadeira', '_bloco'),
        how='left'
    )

    curricula_lines = ["CURRICULA:"]

    for bloco_id, group in merged.groupby('bloco_id'):
        unique_course_ids = set()
        for _, row in group.iterrows():
            if pd.isna(row['abreviatura_cadeira']) or pd.isna(row['docente_id']):
                continue
            unique_id = make_unique_course_id(row['abreviatura_cadeira'], row['docente_id'])
            unique_course_ids.add(unique_id)

        unique_course_ids = sorted(unique_course_ids)
        num_cadeiras = len(unique_course_ids)
        line = f"q{bloco_id} {num_cadeiras} " + " ".join(unique_course_ids)
        curricula_lines.append(line)

    return "\n".join(curricula_lines), merged['bloco_id'].nunique()


def read_teacher_unavailabilities(path, courses_path):

    def get_period(hora):
        period = ((hora.hour - 8) * 60 + hora.minute) // 30
        if period >= 10:
            period -= 2
        return period

    restricoes_df = pd.read_csv(path)
    courses_df = pd.read_csv(courses_path)

    groups = courses_df.groupby('docente_id').agg(list)

    teacher_to_courses = {
        docente_id: [
            make_unique_course_id(abreviatura, docente_id) 
            for abreviatura in groups.loc[docente_id, 'abreviatura']
        ]
        for docente_id in groups.index
    }


    unavailabilities_lines = ["UNAVAILABILITY_CONSTRAINTS:"]

    for _, row in restricoes_df.iterrows():
        docente_id = row['docente_id']
        day = int(row['dia'])
        start_time = pd.to_datetime(row['hora'])
        duration = pd.to_datetime(row['duracao']) - pd.to_datetime("1899-12-30 00:00:00")

        total_minutes = duration.seconds // 60
        num_periods = total_minutes // 30

        start_period = get_period(start_time)
        periods = [start_period + i for i in range(num_periods)]

        courses = teacher_to_courses.get(docente_id, [])
        for course in courses:
            for period in periods:
                unavailabilities_lines.append(f"{course} {day} {period}")

    return "\n".join(unavailabilities_lines), len(restricoes_df)



if __name__ == "__main__":

    csv_rooms = "old_db_test/Salas.csv"
    csv_courses = "old_db_test/Cadeiras.csv"
    blocos_path = "old_db_test/Blocos.csv"
    cadeiras_bloco_path = "old_db_test/Cadeiras por bloco.csv"
    restricoes_path = "old_db_test/Restricoes.csv"

    courses_section, courses_grouped = csv_to_ctt_courses_section(csv_courses)
    rooms_section, room_count = csv_to_ctt_rooms_section(csv_rooms)
    curricula_section, curricula_count = generate_curricula(blocos_path, cadeiras_bloco_path, csv_courses)
    unav_section, constraint_count = read_teacher_unavailabilities(restricoes_path, csv_courses)

    header_lines = [
        "Name: fcup",
        f"Courses: {len(courses_grouped)}",
        f"Rooms: {room_count}",
        "Days: 5",
        "Periods_per_day: 23",
        f"Curricula: {curricula_count}",
        f"Constraints: {constraint_count}"
    ]
    header = "\n".join(header_lines)

    with open("../FlaskAPI/mcts/input/fcup.ctt", "w") as f:
        f.write(header + "\n\n")
        f.write(courses_section + "\n\n")
        f.write(rooms_section + "\n\n")
        f.write(curricula_section + "\n\n")
        f.write(unav_section)
