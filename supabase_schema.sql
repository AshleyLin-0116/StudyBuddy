-- StudyBuddy Database Schema
-- Run this in your Supabase SQL Editor

-- Sessions: logs every study exchange
create table if not exists sessions (
  id          uuid default gen_random_uuid() primary key,
  user_id     text not null,
  messages    jsonb,
  reply       text,
  created_at  timestamp default now()
);

-- Progress: tracks overall stats per user
create table if not exists progress (
  id                 uuid default gen_random_uuid() primary key,
  user_id            text not null unique,
  sessions_count     int default 0,
  questions_answered int default 0,
  streak             int default 0,
  last_studied       date,
  updated_at         timestamp default now()
);

-- Weak spots: tracks topics per course that need more work
create table if not exists weak_spots (
  id         uuid default gen_random_uuid() primary key,
  user_id    text not null,
  course     text not null,
  topic      text not null,
  count      int default 1,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Exam schedule: stores upcoming exam dates and study plans
create table if not exists exams (
  id         uuid default gen_random_uuid() primary key,
  user_id    text not null,
  course     text not null,
  exam_name  text,
  exam_date  date not null,
  exam_time  text,
  topics     text,
  grade      text,
  created_at timestamp default now()
);

-- Uploaded exams: stores practice exams per course
create table if not exists uploaded_exams (
  id         uuid default gen_random_uuid() primary key,
  user_id    text not null,
  course     text not null,
  name       text not null,
  text       text,
  pages      int,
  created_at timestamp default now()
);

-- Practice problems: stores every question, answer, and feedback per course
create table if not exists practice_problems (
  id            uuid default gen_random_uuid() primary key,
  user_id       text not null,
  course        text not null,
  mode          text,
  question      text not null,
  user_answer   text,
  feedback      text,
  weak_spot     boolean default false,
  created_at    timestamp default now()
);