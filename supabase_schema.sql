-- Run this in your Supabase SQL editor to set up StudyBuddy's tables

-- Sessions: logs every study exchange
create table sessions (
  id          uuid default gen_random_uuid() primary key,
  user_id     text not null,
  messages    jsonb,
  reply       text,
  created_at  timestamp default now()
);

-- Progress: tracks overall stats per user
create table progress (
  id               uuid default gen_random_uuid() primary key,
  user_id          text not null unique,
  sessions_count   int default 0,
  questions_answered int default 0,
  streak           int default 0,
  last_studied     date,
  updated_at       timestamp default now()
);

-- Weak spots: tracks topics per course that need more work
create table weak_spots (
  id         uuid default gen_random_uuid() primary key,
  user_id    text not null,
  course     text not null,
  topic      text not null,
  count      int default 1,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Exams: stores upcoming exam dates and study plans
create table exams (
  id         uuid default gen_random_uuid() primary key,
  user_id    text not null,
  course     text not null,
  exam_date  date not null,
  topics     text,
  created_at timestamp default now()
);
